from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)

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
        driver.save_screenshot("error_screenshot.png")
        with open("error_log.txt", "w") as f:
            f.write(str(e))
        return None
    
    finally:
        time.sleep(2)

def extraer_empresas(driver):
    """Extrae la lista de empresas y RFCs de la tabla de despachos/obligaciones."""
    print("Extrayendo lista de empresas...")
    wait = WebDriverWait(driver, 20)
    
    # Esperar a que la tabla se cargue
    print("Esperando a que la tabla se cargue completamente...")
    time.sleep(5)
    
    # Encontrar el contenedor scrolleable específico
    print("Buscando el contenedor de la tabla...")
    scroll_container = driver.find_element(By.CSS_SELECTOR, "div[class*='section-obligations']")
    
    # Lista para almacenar todas las empresas
    todas_las_empresas = []
    altura_scroll = 0
    incremento_scroll = 200  # Reducimos el incremento para capturar mejor los elementos
    intentos_sin_nuevas = 0
    max_intentos_sin_nuevas = 5
    empresas_procesadas = set()  # Conjunto para rastrear empresas ya procesadas
    
    print("Iniciando extracción gradual de empresas...")
    while intentos_sin_nuevas < max_intentos_sin_nuevas:
        # Hacer scroll incrementalmente
        altura_scroll += incremento_scroll
        driver.execute_script(f"arguments[0].scrollTop = {altura_scroll}", scroll_container)
        time.sleep(3)  # Aumentamos el tiempo de espera
        
        # Obtener filas visibles actuales
        filas = driver.find_elements(By.CLASS_NAME, "info")
        empresas_nueva_iteracion = []
        
        # Procesar las empresas visibles
        for fila in filas:
            try:
                # Intentar obtener el nombre de diferentes maneras
                pass  # Implementar lógica para extraer datos de la fila
                
            except Exception as e:
                print(f"Error al procesar fila: {e}")
        
        # Si encontramos nuevas empresas, las añadimos a la lista principal
        if empresas_nueva_iteracion:
            todas_las_empresas.extend(empresas_nueva_iteracion)
            print(f"Total de empresas encontradas hasta ahora: {len(todas_las_empresas)}")
            intentos_sin_nuevas = 0
        else:
            intentos_sin_nuevas += 1
            print(f"Intento sin nuevas empresas: {intentos_sin_nuevas}")
        
        # Guardar progreso parcial
        if empresas_nueva_iteracion:
            df_parcial = pd.DataFrame(todas_las_empresas)
            df_parcial.to_csv('empresas_contalink_parcial.csv', index=False)
            print(f"Guardado progreso parcial con {len(todas_las_empresas)} empresas")
            
        # Scroll hacia arriba un poco para asegurar que no nos saltamos elementos
        if intentos_sin_nuevas > 0:
            driver.execute_script(f"arguments[0].scrollTop = {altura_scroll - 100}", scroll_container)
            time.sleep(1)
    
    print(f"Se encontraron {len(todas_las_empresas)} empresas en total")
    
    # Verificación final de datos
    df_final = pd.DataFrame(todas_las_empresas)
    registros_incompletos = df_final[df_final['nombre'].isna() | df_final['rfc'].isna()].shape[0]
    if registros_incompletos > 0:
        print(f"Advertencia: Se encontraron {registros_incompletos} registros incompletos")
    
    return todas_las_empresas

def limpiar_y_separar_nombre(nombre):
    """Limpia las comillas y separa el régimen de la razón social."""
    # Limpiar comillas dobles
    nombre = nombre.replace('"', '')
    
    # Lista de regímenes conocidos
    regimenes = [
        'S.A. DE C.V.',
        'SA DE CV',
        'S DE RL',
        'S. DE R.L.',
        'SRL DE CV',
        'AC',
        'A.C.',
        'ABP',
        'SAPI DE CV',
        'S.A.P.I. DE C.V.',
        'SPR DE RL DE CV',
        'S.P.R. DE R.L. DE C.V.'
    ]
    
    # Buscar el régimen más largo que coincida
    regimen_encontrado = ''
    razon_social = nombre
    
    for regimen in sorted(regimenes, key=len, reverse=True):
        if nombre.upper().endswith(regimen):
            regimen_encontrado = regimen
            razon_social = nombre[:-len(regimen)].strip(' ,. ')
            break
    
    return razon_social, regimen_encontrado

def verificar_duplicados(rfc, razon_social):
    """Verifica si el RFC o razón social ya existe en Supabase."""
    # Buscar por RFC
    result = supabase.table('contribuyentes').select('*').eq('rfc', rfc).execute()
    if len(result.data) > 0:
        return True
    
    # Buscar por razón social
    result = supabase.table('contribuyentes').select('*').eq('razon_social', razon_social).execute()
    return len(result.data) > 0

def cargar_a_supabase(df):
    """Procesa y carga los datos del DataFrame a Supabase."""
    registros_nuevos = []
    duplicados = []
    
    print("Procesando registros para Supabase...")
    for _, row in df.iterrows():
        if not pd.isna(row['nombre']) and not pd.isna(row['rfc']):
            razon_social, regimen = limpiar_y_separar_nombre(row['nombre'])
            rfc = row['rfc'].strip()
            
            # Determinar tipo de persona basado en la longitud del RFC
            tipo_persona = 'FISICA' if len(rfc) == 13 else 'MORAL' if len(rfc) == 12 else None
            
            if tipo_persona is None:
                continue
            
            # Verificar duplicados
            if not verificar_duplicados(rfc, razon_social):
                registros_nuevos.append({
                    'razon_social': razon_social,
                    'rfc': rfc,
                    'tipo_persona': tipo_persona
                })
            else:
                duplicados.append({
                    'razon_social': razon_social,
                    'rfc': rfc
                })
    
    # Insertar registros nuevos
    if registros_nuevos:
        print(f"Insertando {len(registros_nuevos)} registros nuevos en Supabase...")
        result = supabase.table('contribuyentes').insert(registros_nuevos).execute()
        print("Registros insertados exitosamente")
    else:
        print("No hay nuevos registros para insertar")
    
    # Reportar duplicados
    if duplicados:
        print(f"\nSe encontraron {len(duplicados)} registros duplicados:")
        for dup in duplicados:
            print(f"- {dup['razon_social']} ({dup['rfc']})")

# Función principal
if __name__ == "__main__":
    driver = login_contalink("f.anastasio@gs.com.mx", "6W&3jhU,ugwaTNU")
    if driver:
        try:
            print("Sesión iniciada correctamente")
            empresas = extraer_empresas(driver)
            
            # Crear DataFrame y guardar en CSV
            df = pd.DataFrame(empresas)
            df.to_csv('empresas_contalink.csv', index=False)
            print("Datos guardados en empresas_contalink.csv")
            
            # Cargar datos a Supabase
            cargar_a_supabase(df)
            print("\nProceso completado!")
            
        finally:
            driver.quit()