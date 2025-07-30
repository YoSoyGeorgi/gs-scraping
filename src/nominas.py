#file: /gs-scraping/gs-scraping/src/nominas.py

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import os
import time

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def login_contalink(username, password):
    """Inicia sesión en Contalink en modo headless usando GeckoDriver local."""
    gecko_driver_path = "geckodriver.exe"  # Ruta al archivo de geckodriver en tu máquina
    service = Service(gecko_driver_path)
    
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")  # Comentado para ver el proceso
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        print("Abriendo la página de login...")
        driver.get("https://app.contalink.com/login")
        
        wait = WebDriverWait(driver, 20)
        email_input = wait.until(EC.presence_of_element_located((By.ID, "usuario_email")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "usuario_password")))
        
        print("Ingresando usuario y contraseña...")
        email_input.send_keys(username)
        password_input.send_keys(password)
        
        login_button = wait.until(EC.element_to_be_clickable((By.NAME, "commit")))
        login_button.click()
        
        try:
            popup = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sweet-alert.showSweetAlert.visible")))
            popup_button = popup.find_element(By.CSS_SELECTOR, "button.confirm")
            popup_button.click()
            print("Pop-up cerrado.")
        except Exception:
            print("No apareció el pop-up.")
        
        print("Esperando a que cargue el dashboard...")
        wait.until(EC.url_contains("despachos/obligaciones"))
        print("Inicio de sesión exitoso!")
        return driver
    
    except Exception as e:
        print(f"Error: {e}")
        driver.quit()
        return None

def obtener_contribuyentes():
    """Obtiene los contribuyentes de Supabase."""
    response = supabase.table('contribuyentes').select('contribuyente_id, rfc').execute()
    return response.data

def buscar_rfc(driver, rfc):
    try:
        wait = WebDriverWait(driver, 20)
        
        # Esperar a que la página cargue completamente
        time.sleep(5)
        
        # Intentar encontrar el input de búsqueda
        input_rfc = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='rfc']")))
        
        # Hacer scroll hacia el elemento usando JavaScript
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", input_rfc)
        time.sleep(2)
        
        # Intentar limpiar usando JavaScript
        driver.execute_script("arguments[0].value = '';", input_rfc)
        time.sleep(1)
        
        # Enviar las teclas usando JavaScript y luego con send_keys como respaldo
        driver.execute_script(f"arguments[0].value = '{rfc}';", input_rfc)
        input_rfc.send_keys(Keys.CONTROL + "a")  # Seleccionar todo
        input_rfc.send_keys(rfc)  # Escribir el RFC
        
        time.sleep(3)
        
        # Buscar y hacer clic en el elemento RFC usando diferentes estrategias
        try:
            # Implementar lógica para buscar el RFC
            pass
        except:
            pass
        
        # Hacer scroll al elemento encontrado
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elemento_rfc)
        time.sleep(2)
        
        # Intentar hacer clic usando JavaScript
        driver.execute_script("arguments[0].click();", elemento_rfc)
        
        time.sleep(5)
        
        if "ingresos" in driver.current_url:
            # Implementar lógica si se encuentra el RFC
            pass
        else:
            pass
    
    except Exception as e:
        print(f"Error al buscar RFC {rfc}: {e}")
        return False

def descargar_comprobantes(driver, rfc):
    try:
        wait = WebDriverWait(driver, 30)
        
        print(f"Navegando a la página de comprobantes para RFC: {rfc}")
        driver.get("https://app.contalink.com/app/nomina/comprobantes")
        
        print("Esperando a que cargue completamente la información...")
        time.sleep(10)
        
        # driver.save_screenshot(f"comprobantes_{rfc}_1.png")
        
        try:
            # Implementar lógica para descargar comprobantes
            pass
        except Exception as e:
            pass
        
        print("Aplicando filtros...")
        boton_filtro = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.ng-star-inserted")))
        boton_filtro.click()
        time.sleep(2)

        # Configurar fechas (mes actual)
        primer_dia = f"2025-01-01"
        ultimo_dia = f"2025-06-30"  # Simplificado, podría mejorarse para considerar el último día real
        
        # Seleccionar campos de fecha
        campos_fecha = driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
        if len(campos_fecha) >= 2:
            # Implementar lógica para establecer fechas
            pass
        
        # Hacer clic en Aplicar usando el selector CSS exacto
        print("Haciendo clic en botón Aplicar...")
        try:
            # Implementar lógica para aplicar filtros
            pass
        except Exception as e:
            pass
        
        # Hacer clic en el botón
        print("Haciendo clic en el botón Aplicar...")
        driver.execute_script("arguments[0].click();", boton_aplicar)
        print("Clic en Aplicar ejecutado")
        
        # Esperar un tiempo fijo después de aplicar filtros
        print("Esperando 10 segundos para que se carguen los datos filtrados...")
        time.sleep(10)  # Espera fija de 10 segundos
        
        # Hacer clic en el botón de descarga
        print("Haciendo clic en botón de descarga...")
        boton_descarga = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.tw-button-grid.ng-star-inserted")))
        boton_descarga.click()
        time.sleep(2)
        
        # Seleccionar opción de Excel
        opcion_excel = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#download-excel")))
        opcion_excel.click()
        
        # Hacer clic en el botón Descargar
        boton_descargar = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Descargar']")))
        boton_descargar.click()
        time.sleep(3)
        
        driver.get("https://app.contalink.com/app/general/descargas")
        time.sleep(5)
        
        # Hacer clic en el botón de descarga del primer elemento
        boton_descarga_reporte = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.tw-button.button-primary-25")))
        boton_descarga_reporte.click()
        time.sleep(10)  # Esperar a que se descargue el archivo
        
        print(f"Comprobantes descargados exitosamente para RFC: {rfc}")
        return True
    
    except Exception as e:
        print(f"Error al descargar comprobantes para RFC {rfc}: {e}")
        return False

def mover_ultimo_archivo_descargado(rfc):
    """Mueve el último archivo descargado a una carpeta específica."""
    try:
        # Obtener directorio de descargas
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Buscar el archivo más reciente con extensión .xlsx
        archivos = glob.glob(os.path.join(download_dir, "*.xlsx"))
        if not archivos:
            return
        
        ultimo_archivo = max(archivos, key=os.path.getctime)
        
        # Crear carpeta para el RFC si no existe
        carpeta_destino = os.path.join(os.getcwd(), "comprobantes", rfc)
        os.makedirs(carpeta_destino, exist_ok=True)
        
        # Nombre del archivo destino con fecha
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_destino = os.path.join(carpeta_destino, f"{rfc}_{fecha_actual}.xlsx")
        
        # Mover archivo
        os.rename(ultimo_archivo, archivo_destino)
        print(f"Archivo movido exitosamente a: {archivo_destino}")

    except Exception as e:
        print(f"Error al mover el archivo: {e}")

def procesar_archivo_nomina(archivo_excel, contribuyente_id):
    """Procesa el archivo Excel descargado y sube los datos a Supabase."""
    try:
        # Implementar lógica para procesar el archivo
        pass
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")

def proceso_completo():
    """Ejecuta el proceso completo de descarga de comprobantes para todos los contribuyentes."""
    try:
        driver = login_contalink("f.anastasio@gs.com.mx", "6W&3jhU,ugwaTNU")
        if driver:
            try:
                print("Sesión iniciada correctamente")
                contribuyentes = obtener_contribuyentes()
                
                for contribuyente in contribuyentes:
                    rfc = contribuyente['rfc']
                    descargar_comprobantes(driver, rfc)
                    mover_ultimo_archivo_descargado(rfc)
                
                print("Proceso completado!")
            finally:
                driver.quit()
    except Exception as e:
        print(f"Error en el proceso completo: {e}")

# Ejecutar el proceso completo
if __name__ == "__main__":
    proceso_completo()