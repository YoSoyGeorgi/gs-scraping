# File: /gs-scraping/gs-scraping/src/opinion_cumplimiento.py

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define el directorio de descarga globalmente
download_dir = os.path.join(os.getcwd(), "descargas")

def get_latest_pdf():
    """Obtiene el archivo PDF más reciente en el directorio de descargas."""
    list_of_files = glob.glob(os.path.join(download_dir, '*.pdf'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def upload_to_supabase(file_path, rfc):
    """Sube el archivo a Supabase Storage y retorna la URL."""
    try:
        bucket_name = "opiniones"
        file_name = f"opinion_cumplimiento_{rfc}_{int(time.time())}.pdf"
        
        # Configurar cliente Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Subir archivo
        with open(file_path, "rb") as f:
            response = (
                supabase.storage
                .from_(bucket_name)
                .upload(
                    file=f,
                    path=file_name,
                    file_options={"cache-control": "3600", "upsert": "true"}
                )
            )
        
        # Construir la URL del archivo
        file_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_name}"
        print(f"Archivo subido exitosamente: {file_url}")
        return file_url
    except Exception as e:
        print(f"Error al subir archivo a Supabase: {e}")
        return None

def get_contribuyente_id(rfc):
    """Obtiene el contribuyente_id basado en el RFC."""
    try:
        response = supabase.table('contribuyentes_imp').select('contribuyente_id').eq('rfc', rfc).execute()
        if response.data:
            return response.data[0]['contribuyente_id']
        print(f"No se encontró contribuyente con RFC: {rfc}")
        return None
    except Exception as e:
        print(f"Error al buscar contribuyente_id: {e}")
        return None

def create_opinion_record(opinion_url, contribuyente_id):
    """Crea un registro en la tabla opiniones."""
    try:
        data = {
            'opinion_cumplimiento': opinion_url,
            'contribuyente_id': contribuyente_id
        }
        response = supabase.table('opiniones_imp').insert(data).execute()
        print("Registro creado exitosamente en la tabla opiniones")
        return True
    except Exception as e:
        print(f"Error al crear registro en opiniones: {e}")
        return False

def login_contalink(username, password):
    """Inicia sesión en Contalink en modo headless usando GeckoDriver local."""
    gecko_driver_path = "geckodriver.exe"
    service = Service(gecko_driver_path)
    
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    options.set_preference("pdfjs.disabled", True)

    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        print("Iniciando sesión en Contalink...")
        driver.get("https://app.contalink.com/login")
        
        wait = WebDriverWait(driver, 20)
        email_input = wait.until(EC.presence_of_element_located((By.ID, "usuario_email")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "usuario_password")))
        
        email_input.send_keys(username)
        password_input.send_keys(password)
        
        login_button = wait.until(EC.element_to_be_clickable((By.NAME, "commit")))
        login_button.click()
        
        try:
            popup = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sweet-alert.showSweetAlert.visible")))
            popup_button = popup.find_element(By.CSS_SELECTOR, "button.confirm")
            popup_button.click()
        except:
            print("No se encontró pop-up, continuando...")
        
        wait.until(EC.url_contains("despachos/obligaciones"))
        print("Inicio de sesión exitoso!")
        return driver
    
    except Exception as e:
        print(f"Error durante el login: {e}")
        driver.quit()
        return None

def scroll_into_view(driver, element):
    """Hace scroll hasta que el elemento sea visible."""
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(1)  # Dar tiempo para que el scroll se complete

def retry_operation(func, max_attempts=3):
    """Reintenta una operación varias veces antes de fallar."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            print(f"Intento {attempt + 1} falló, reintentando...")
            time.sleep(2)

def op_cump(username, password):
    """Procesa las opiniones de cumplimiento para todos los contribuyentes."""
    driver = login_contalink(username, password)
    if not driver:
        print("No se pudo iniciar sesión")
        return

    try:
        # Obtener todos los contribuyentes de Supabase
        response = supabase.table('contribuyentes_imp').select('contribuyente_id, rfc').execute()
        contribuyentes = response.data
        
        if not contribuyentes:
            print("No se encontraron contribuyentes en Supabase")
            driver.quit()
            return
            
        print(f"Se encontraron {len(contribuyentes)} contribuyentes para procesar")
        
        for contribuyente in contribuyentes:
            rfc = contribuyente['rfc']
            print(f"\nProcesando RFC: {rfc}")
            
            try:
                # Asegurarse de estar en la página principal
                driver.get("https://app.contalink.com/app/despachos/obligaciones")
                time.sleep(5)
                
                wait = WebDriverWait(driver, 20)
                
                def buscar_y_llenar_rfc():
                    search_input = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[formcontrolname='rfc']")))
                    scroll_into_view(driver, search_input)
                    search_input.clear()
                    time.sleep(1)
                    search_input.send_keys(rfc)
                    return search_input
                
                # Intentar buscar y llenar el RFC con reintentos
                search_input = retry_operation(buscar_y_llenar_rfc)
                
                time.sleep(3)
                
                # Buscar la empresa con el RFC
                companies = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.info.ng-star-inserted")))
                
                rfc_encontrado = False
                for company in companies:
                    try:
                        rfc_element = company.find_element(By.CLASS_NAME, "rfc")
                        if rfc_element.text.strip() == rfc:
                            print(f"RFC {rfc} encontrado, descargando opinión...")
                            rfc_encontrado = True

                    except Exception as e:
                        print(f"Error al procesar compañía: {e}")
                        continue
                
                if not rfc_encontrado:
                    print(f"No se encontró el RFC: {rfc}")
                
                print("Regresando a la página principal para el siguiente RFC...")
                
            except Exception as e:
                print(f"Error procesando RFC {rfc}: {e}")
                # Intentar refrescar la página en caso de error
                try:
                    driver.refresh()
                    time.sleep(5)
                except:
                    pass
                continue
            
    except Exception as e:
        print(f"Error durante el proceso: {e}")
    finally:
        print("\nCerrando el navegador...")
        driver.quit()

# Ejecutar el script
if __name__ == "__main__":
    op_cump("Impuestos@gs.com.mx", "**sexaT$$")