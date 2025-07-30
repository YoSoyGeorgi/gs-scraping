from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time
import re

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def extraer_tabla(driver):
    """Extrae la información de la tabla de ingresos a un DataFrame."""
    try:
        # Esperar a que la tabla esté presente
        wait = WebDriverWait(driver, 10)
        tabla = wait.until(EC.presence_of_element_located((By.ID, "invoices-grid-table")))

        # Extraer las cabeceras de la tabla
        cabeceras = tabla.find_elements(By.TAG_NAME, "th")
        
        # Filtrar cabeceras relevantes (eliminar vacías o innecesarias)
        columnas = [cabecera.text.strip() for cabecera in cabeceras if cabecera.text.strip() != ""]
        
        # Limitar a las primeras 9 cabeceras relevantes
        columnas = columnas[:9]
        
        print(f"Cabeceras extraídas: {columnas}")  # Depuración para verificar las cabeceras

        # Extraer las filas de la tabla desde <tbody> (filas de datos)
        filas = tabla.find_elements(By.XPATH, ".//tbody/tr")
        datos = []
        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            
            # Depuración: Imprimir la cantidad y contenido de celdas
            print(f"Cantidad de celdas: {len(celdas)}")
            print(f"Celdas: {[celda.text.strip() for celda in celdas]}")  # Imprime el texto de las celdas
            
            # Asegurarse de que la fila tenga al menos 8 celdas (en algunos casos puede haber más o menos celdas)
            if len(celdas) >= 8:
                # Obtener solo las primeras 8 celdas (con el texto)
                datos.append([celda.text.strip() for celda in celdas[:9]])
            else:
                # Depuración: Imprimir el número de celdas en las filas que son ignoradas
                print(f"Fila ignorada debido a un número de celdas incorrecto: {len(celdas)}")
        
        # Crear el DataFrame solo si hay datos
        if datos:
            df = pd.DataFrame(datos, columns=columnas)
            print("Datos extraídos con éxito")
            return df
        else:
            print("No se extrajeron datos válidos.")
            return None

    except Exception as e:
        print(f"Error al extraer los datos de la tabla: {e}")
        return None






def login_contalink(username, password):
    """Inicia sesión en Contalink en modo headless usando GeckoDriver local."""
    gecko_driver_path = "geckodriver.exe"  # Ruta al archivo de geckodriver en tu máquina
    service = Service(gecko_driver_path)
    
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")  # Ejecutar en segundo plano
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
        driver.save_screenshot("error_screenshot.png")
        with open("error_log.txt", "w") as f:
            f.write(str(e))
    
    finally:
        import time
        time.sleep(2)

def filtrar_por_fecha(driver, desde, hasta):
    """Hace clic en el botón de filtros, ingresa fechas y aplica el filtro."""
    try:
        wait = WebDriverWait(driver, 10)

        # Hacer clic en el botón de filtros
        print("Buscando el botón de filtros...")
        filtro_boton = wait.until(EC.element_to_be_clickable((By.ID, "grid-filters")))
        filtro_boton.click()
        print("Botón de filtros clickeado con éxito.")

        # Ingresar fecha "Desde" usando JavaScript
        print(f"Ingresando fecha desde: {desde}")
        fecha_desde = wait.until(EC.presence_of_element_located((By.ID, "starting-date")))
        driver.execute_script("arguments[0].value = arguments[1]", fecha_desde, desde)

        # Ingresar fecha "Hasta" usando JavaScript
        print(f"Ingresando fecha hasta: {hasta}")
        fecha_hasta = wait.until(EC.presence_of_element_located((By.ID, "ending-date")))
        driver.execute_script("arguments[0].value = arguments[1]", fecha_hasta, hasta)

        # Hacer clic en "Aplicar"
        print("Aplicando filtro...")
        aplicar_boton = wait.until(EC.element_to_be_clickable((By.ID, "apply-grid-filters")))
        aplicar_boton.click()
        print("Filtro aplicado con éxito.")

    except Exception as e:
        print(f"Error al aplicar el filtro: {e}")

def acceder_ingresos(username, password, rfc, desde, hasta):
    """Inicia sesión, accede a la página de ingresos y aplica un filtro por fecha."""
    driver = login_contalink(username, password)
    if driver:
        ingresos_url = f"https://app.contalink.com/ingresos/{rfc}"
        print(f"Accediendo a: {ingresos_url}")
        driver.get(ingresos_url)
        
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print(f"Acceso exitoso a la página de ingresos de {rfc}")

            # Aplicar el filtro de fechas
            filtrar_por_fecha(driver, desde, hasta)

            # Extraer la tabla a un DataFrame
            df = extraer_tabla(driver)
            if df is not None:
                print(df)
                insertar_earnings(df, rfc)
                driver.quit()
        
        except Exception as e:
            print(f"Error al acceder a la página o aplicar filtros: {e}")
        
        return driver
    return None

def obtener_contribuyente_id(rfc):
    try:
        response = supabase.table("contribuyentes").select("contribuyente_id").eq("rfc", rfc).execute()
        if response.data:
            return response.data[0]["contribuyente_id"]
        else:
            print(f"No se encontró el contribuyente con RFC: {rfc}")
            return None
    except Exception as e:
        print(f"Error al obtener contribuyente_id: {e}")
        return None

def insertar_earnings(df, rfc):
    contribuyente_id = obtener_contribuyente_id(rfc)
    if contribuyente_id is None:
        return

    for index, row in df.iterrows():
        # Convertir el valor de 'Total' a un formato numérico
        importe = row["Total"].replace("$", "").replace(",", "")
        try:
            importe = float(importe)
        except ValueError as e:
            print(f"Error al convertir el importe: {e}")
            continue

        data = {
            "contribuyente_id": contribuyente_id,
            "rfc": row["RFC"],
            "razon_social": row["Cliente"],
            "fecha_emision": row["Fecha"],
            "importe": importe,
            "tipo": "INGRESO"
        }
        try:
            response = supabase.table("earnings").insert(data).execute()
            # Verificar si hay datos en la respuesta
            if response.data:
                print(f"Datos insertados correctamente para RFC: {row['RFC']}")
            else:
                print(f"Error al insertar datos para RFC: {row['RFC']}")
        except Exception as e:
            print(f"Error al insertar datos: {e}")

def obtener_rfcs_desde_supabase():
    """Obtiene la lista de RFCs desde Supabase."""
    try:
        response = supabase.table("contribuyentes").select("rfc").execute()
        if response.data:
            return [item["rfc"] for item in response.data]
        return []
    except Exception as e:
        print(f"Error al obtener RFCs desde Supabase: {e}")
        return []

def buscar_y_seleccionar_rfc(driver, rfc):
    """Busca y selecciona un RFC específico en la página."""
    try:
        wait = WebDriverWait(driver, 10)
        
        # Esperar a que el campo sea visible
        input_rfc = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, 
            "input[formcontrolname='rfc']"
        )))
        
        # Hacer scroll al campo usando JavaScript
        driver.execute_script("arguments[0].scrollIntoView(true);", input_rfc)
        time.sleep(0.5)  # Pequeña pausa para asegurar el scroll
        
        input_rfc.clear()
        input_rfc.send_keys(rfc)
        
        # Esperar y hacer clic en el resultado de la búsqueda
        resultado = wait.until(EC.element_to_be_clickable((
            By.XPATH, 
            f"//div[contains(text(), '{rfc}')]"
        )))
        resultado.click()
        return True
    except Exception as e:
        print(f"Error al buscar/seleccionar RFC {rfc}: {e}")
        return False

def obtener_total_registros(driver):
    """Obtiene el número total de registros en la tabla."""
    try:
        info_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "invoices-grid-table_info"))
        )
        texto_info = info_element.text
        # El texto suele ser "Mostrando 1 a 10 de 45 registros"
        match = re.search(r'de (\d+) registros', texto_info)
        if match:
            return int(match.group(1))
        return 0
    except Exception as e:
        print(f"Error al obtener total de registros: {e}")
        return 0

def hay_siguiente_pagina(driver):
    """Verifica si existe un botón 'Siguiente' activo."""
    try:
        siguiente = driver.find_element(By.ID, "invoices-grid-table_next")
        return "disabled" not in siguiente.get_attribute("class")
    except:
        return False

def extraer_todas_paginas(driver):
    """Extrae datos de todas las páginas de la tabla."""
    all_data = []
    
    try:
        # Esperar a que la información de la tabla esté presente
        info_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "invoices-grid-table_info"))
        )
        texto_info = info_element.text
        print(f"Información de la tabla: {texto_info}")
        
        pagina = 1
        while True:
            print(f"\nProcesando página {pagina}")
            
            # Esperar a que la tabla se cargue
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "invoices-grid-table"))
            )
            time.sleep(2)  # Dar tiempo adicional para que los datos se carguen
            
            # Extraer datos de la página actual
            df_pagina = extraer_tabla(driver)
            if df_pagina is not None and not df_pagina.empty:
                print(f"Extraídos {len(df_pagina)} registros de la página {pagina}")
                all_data.append(df_pagina)
            else:
                print(f"No se encontraron datos en la página {pagina}")
            
            # Verificar si hay siguiente página
            try:
                siguiente_boton = driver.find_element(By.ID, "invoices-grid-table_next")
                if "disabled" in siguiente_boton.get_attribute("class"):
                    print("No hay más páginas disponibles")
                    break
                
                print("Haciendo clic en 'Siguiente'...")
                siguiente_boton.click()
                time.sleep(3)  # Esperar a que la siguiente página cargue
                pagina += 1
                
            except Exception as e:
                print(f"Error al navegar a la siguiente página: {e}")
                break
    
    except Exception as e:
        print(f"Error durante la extracción de páginas: {e}")
    
    # Combinar todos los DataFrames
    if all_data:
        df_final = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal de registros extraídos: {len(df_final)}")
        return df_final
    
    print("No se encontraron datos para combinar")
    return None

def procesar_todos_rfcs(username, password):
    """Procesa todos los RFCs de manera recursiva."""
    driver = login_contalink(username, password)
    if not driver:
        return
    
    rfcs = obtener_rfcs_desde_supabase()
    print(f"RFCs a procesar: {len(rfcs)}")
    
    for rfc in rfcs:
        try:
            print(f"\nProcesando RFC: {rfc}")
            
            # Ir a la página principal
            driver.get("https://app.contalink.com/app/despachos/obligaciones")
            time.sleep(2)
            
            # Buscar y seleccionar el RFC
            if not buscar_y_seleccionar_rfc(driver, rfc):
                continue
            
            # Aplicar filtros de fecha
            filtrar_por_fecha(driver, "2025-01-01", "2025-07-30")  # Ajusta las fechas según necesites
            
            # Extraer datos de todas las páginas
            df_completo = extraer_todas_paginas(driver)
            
            if df_completo is not None:
                insertar_earnings(df_completo, rfc)
                print(f"Procesamiento completado para RFC: {rfc}")
            
        except Exception as e:
            print(f"Error procesando RFC {rfc}: {e}")
            continue
    
    driver.quit()

# Modificar la llamada principal
if __name__ == "__main__":
    procesar_todos_rfcs("f.anastasio@gs.com.mx", "6W&3jhU,ugwaTNU")

