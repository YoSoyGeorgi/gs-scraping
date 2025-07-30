from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from selenium.webdriver.common.action_chains import ActionChains
from supabase import create_client, Client
from datetime import datetime
import os
import pandas as pd

# Cargar variables de entorno
load_dotenv()

def procesar_archivo_excel(ruta_archivo):
    """Procesa el archivo Excel descargado y retorna un DataFrame limpio."""
    print("Procesando archivo Excel...")
    try:
        # Leer todas las filas del archivo Excel
        df = pd.read_excel(ruta_archivo, header=None)
        
        # Buscar en la columna B (índice 1) la primera fila con contenido
        inicio_tabla = None
        for idx, valor in enumerate(df[1]):            
            if pd.notna(valor):
                inicio_tabla = idx
                break

        if inicio_tabla is not None:
            df_clean = df.iloc[inicio_tabla:]
            return df_clean.reset_index(drop=True)
        else:
            print("No se encontró contenido en el archivo.")
            return None
            
    except Exception as e:
        print(f"Error al procesar el archivo Excel: {e}")
        return None

def login_runa(username, password):
    """Inicia sesión en RunaHR y descarga el archivo de empleados."""
    gecko_driver_path = "geckodriver.exe"
    service = Service(gecko_driver_path)
    
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")  # Comentado para debug visual
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    # Configurar la carpeta de descargas
    downloads_path = os.path.join(os.getcwd(), "descargas")
    if not os.path.exists(downloads_path):
        os.makedirs(downloads_path)
    
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", downloads_path)
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.ms-excel,application/csv,text/csv")

    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        print("Abriendo la página de login...")
        driver.get("https://gonzalez-solis.runahr.com/login")
        
        wait = WebDriverWait(driver, 20)
        
        # Login
        print("Ingresando credenciales...")
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        
        email_input.send_keys(username)
        password_input.send_keys(password)
        
        # Clic en botón de login
        login_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@type='submit']//span[contains(text(), 'Ingresar')]")))
        login_button.click()
        
        print("Esperando redirección...")
        time.sleep(5)  # Esperar redirección
        
        # Ir a la lista de empleados
        print("Navegando a la lista de empleados...")
        driver.get("https://gonzalez-solis.runahr.com/employees/list")
        time.sleep(3)
        
        # Intentar cerrar el video emergente si aparece
        try:
            close_video_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cerrar')]")))
            close_video_button.click()
        except Exception as e:
            print("No se encontró video emergente, continuando...")
        
        # Clic en "Más acciones"
        print("Haciendo clic en 'Más acciones'...")
        more_actions_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Más acciones')]")))
        more_actions_button.click()
        time.sleep(2)  # Esperar a que el menú se despliegue
        
        # Tomar captura de pantalla para debug
        print("Tomando captura de pantalla del menú...")
        driver.save_screenshot("menu_debug.png")
        
        # Clic en "Edición masiva de empleados"
        print("Seleccionando 'Edición masiva de empleados'...")
        mass_edit_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@class='item' and contains(., 'Edición masiva de empleados')]")))
        
        # Intentar diferentes métodos de clic
        try:
            mass_edit_option.click()
        except Exception as e:
            print(f"Error al hacer clic en 'Edición masiva de empleados': {e}")
        
        time.sleep(2)
        
        # Iterar sobre las pestañas
        tabs = ['Personal', 'Empleo', 'Pago']
        for tab in tabs:
            print(f"Haciendo clic en la pestaña {tab}...")
            tab_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{tab}')]")))
            tab_button.click()
            time.sleep(1)
        
        # Clic en continuar
        print("Haciendo clic en 'Continuar'...")
        continue_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button//span[contains(text(), 'continuar')]")))
        continue_button.click()
        
        # Esperar a que se complete la descarga
        print("Esperando la descarga del archivo...")
        download_file_path = os.path.join(downloads_path, "Formato_carga_masiva_de_empleados.xlsx")
        while not os.path.exists(download_file_path):
            time.sleep(1)
        
        print("¡Descarga completada! Cerrando el navegador...")
        driver.quit()
        
        # Procesar el archivo descargado
        df_empleados = procesar_archivo_excel(download_file_path)
        if df_empleados is not None:
            return df_empleados
        
        return None
        
    except Exception as e:
        print(f"Error durante el proceso: {e}")
        driver.save_screenshot("error_screenshot.png")
        return None

def sincronizar_con_supabase(df):
    """
    Sincroniza los datos del DataFrame con Supabase
    """
    # Configurar cliente Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Método radical: convertir todo el DataFrame a una lista de diccionarios Python puros
    # y reemplazar los valores NaN por None para evitar problemas
    df_clean = df.fillna('')  # Reemplazar NaN con cadenas vacías
    registros = []
    
    # Asegurarse de que estamos trabajando con valores simples, no con Series de pandas
    records_list = df_clean.to_dict('records')
    
    for record in records_list:
        registro = {}
        for col, valor in record.items():
            registro[col] = valor
        registros.append(registro)
    
    total_filas = len(registros)
    print(f"\nIniciando sincronización de {total_filas} registros...")
    
    # Obtener todos los emails de Runa
    emails_runa = set()
    for registro in registros:
        email = str(registro.get('Email corporativo', '')).strip()
        if email and email.lower() != 'nan':
            emails_runa.add(email.lower())
    
    # Obtener todos los empleados de Supabase
    response = supabase.table('employees').select('email, employee_id').execute()
    empleados_supabase = response.data
    
    # Identificar empleados a eliminar (están en Supabase pero no en Runa)
    empleados_a_eliminar = []
    for empleado in empleados_supabase:
        if empleado['email'] not in emails_runa:
            empleados_a_eliminar.append(empleado['employee_id'])
    
    # Eliminar empleados que ya no están en Runa
    if empleados_a_eliminar:
        print(f"\nEliminando {len(empleados_a_eliminar)} empleados que ya no están en Runa...")
        for employee_id in empleados_a_eliminar:
            supabase.table('employees').delete().eq('employee_id', employee_id).execute()
    
    # Ahora trabajamos con diccionarios Python puros, no con objetos de pandas
    for i, registro in enumerate(registros):
        print(f"\nProcesando registro {i + 1} de {total_filas}")
        
        # Extraer datos del diccionario puro
        email_corporativo = str(registro.get('Email corporativo', '')).strip()
        
        if not email_corporativo or email_corporativo.lower() == 'nan':
            print("Email corporativo no válido, omitiendo registro.")
            continue
        
        # Verificar si el sueldo es 99
        num_hijos_str = str(registro.get('Número de hijos', '')).strip()
        try:
            num_hijos = int(num_hijos_str)
        except (ValueError, TypeError):
            num_hijos = 0
        
        # Para debug, mostrar todas las claves disponibles
        print("Todas las claves disponibles en orden:")
        for idx, key in enumerate(registro.keys()):
            print(f"{idx}: {key}")
        
        # Identificar específicamente la columna de Nombre que está entre RFC y Apellido paterno
        columna_nombre_correcta = None
        columnas_list = list(registro.keys())
        
        # Buscar la posición de RFC y Apellido paterno
        try:
            rfc_index = columnas_list.index('RFC')
            apellido_paterno_index = columnas_list.index('Apellido paterno')
            columna_nombre_correcta = columnas_list[rfc_index + 1]  # Asumiendo que el nombre está justo después del RFC
        except ValueError:
            print("No se encontró la columna de RFC o Apellido paterno.")
        
        # Si no encontramos por posición, usamos la primera columna que contiene "Nombre"
        if not columna_nombre_correcta:
            for col in columnas_list:
                if 'Nombre' in col:
                    columna_nombre_correcta = col
                    break
        
        print(f"Usando columna de nombre: '{columna_nombre_correcta}'")
        
        # Obtener los valores como strings simples
        nombre = str(registro.get(columna_nombre_correcta, '')).strip()
        apellido_paterno = str(registro.get('Apellido paterno', '')).strip()
        apellido_materno = str(registro.get('Apellido materno', '')).strip()
        apellido_completo = f"{apellido_paterno} {apellido_materno}".strip()
        
        # Otros campos
        reportar_a = str(registro.get('Reportar a', '')).strip()
        area = str(registro.get('Área', '')).strip()