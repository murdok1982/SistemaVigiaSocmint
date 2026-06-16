import os
import urllib.request
import json
import subprocess
import shutil

section = """
---

## 🎖️ CENTRO DE COMUNICACIONES Y REPORTES OFICIALES
**NIVEL DE ACCESO:** AUTORIZADO | **DESTINATARIO:** COMANDANCIA DE DESARROLLO (gustavolobatoclara@gmail.com)

A través del siguiente portal de comunicaciones, el personal autorizado puede emitir reportes de incidencias, fallas críticas en despliegue (compilación) o solicitudes de mejoras estratégicas. Seleccione la directiva correspondiente para visualizar los protocolos de envío:

<details>
<summary><b>🚨 REPORTAR QUEJA O INCIDENCIA DISCIPLINARIA / OPERATIVA</b></summary>
<br>
Para tramitar una queja sobre el funcionamiento, estructura o contenido del sistema, envíe un mensaje a <b>gustavolobatoclara@gmail.com</b> siguiendo este protocolo:
<ol>
  <li><b>Asunto:</b> [QUEJA] - Nombre del Sistema - Breve descripción.</li>
  <li><b>Cuerpo del mensaje:</b> Detallar claramente la incidencia, impacto operativo y, si es posible, la evidencia (capturas o logs).</li>
  <li><b>Prioridad:</b> Indicar si es de atención inmediata o diferida.</li>
</ol>
</details>

<details>
<summary><b>🛠️ REPORTE DE PROBLEMAS DE COMPILACIÓN O DESPLIEGUE</b></summary>
<br>
Si experimenta fallos durante la fase de compilación o instalación del sistema, reporte a <b>gustavolobatoclara@gmail.com</b> con la siguiente estructura técnica:
<ol>
  <li><b>Asunto:</b> [COMPILACIÓN] - Falla en entorno &lt;Entorno/OS&gt;.</li>
  <li><b>Especificaciones:</b> Sistema Operativo, versión de dependencias y herramientas de compilación utilizadas.</li>
  <li><b>Traza de Error (Logs):</b> Adjunte el log completo de errores proporcionado por la terminal (en formato texto o captura legible).</li>
  <li><b>Pasos de Reproducción:</b> Secuencia exacta de comandos ejecutados antes del fallo crítico.</li>
</ol>
</details>

<details>
<summary><b>💡 SUGERENCIAS O SOLICITUDES DE DESARROLLO</b></summary>
<br>
Para proponer nuevas capacidades tácticas, módulos de inteligencia o mejoras de arquitectura, envíe su solicitud a <b>gustavolobatoclara@gmail.com</b>:
<ol>
  <li><b>Asunto:</b> [PROPUESTA] - Mejora o Nuevo Módulo.</li>
  <li><b>Objetivo Táctico:</b> ¿Qué problema resuelve o qué ventaja proporciona esta nueva característica?</li>
  <li><b>Viabilidad:</b> (Opcional) Posible enfoque técnico o herramientas recomendadas para su implementación.</li>
</ol>
</details>

---
"""

def update_repos():
    req = urllib.request.Request('https://api.github.com/users/murdok1982/repos?per_page=100', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req)
    repos = json.loads(resp.read().decode('utf-8'))
    
    temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'github_repos_update')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    updated_count = 0
    for repo in repos:
        clone_url = repo['clone_url']
        name = repo['name']
        print(f"Processing {name}...")
        
        repo_path = os.path.join(temp_dir, name)
        
        try:
            if os.path.exists(repo_path):
                subprocess.run(['git', '-C', repo_path, 'pull', '--rebase'], check=True, capture_output=True)
            else:
                subprocess.run(['git', 'clone', clone_url, repo_path], check=True, capture_output=True)
            
            readme_path = os.path.join(repo_path, 'README.md')
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if "CENTRO DE COMUNICACIONES Y REPORTES OFICIALES" not in content:
                    with open(readme_path, 'a', encoding='utf-8') as f:
                        f.write(section)
                    
                    subprocess.run(['git', '-C', repo_path, 'add', 'README.md'], check=True)
                    subprocess.run(['git', '-C', repo_path, 'commit', '-m', 'Añadido Centro de Comunicaciones Militar'], check=True)
                    subprocess.run(['git', '-C', repo_path, 'push'], check=True)
                    updated_count += 1
                    print(f"Updated and pushed {name}")
                else:
                    print(f"Already updated {name}")
            else:
                print(f"No README.md in {name}")
                
        except Exception as e:
            print(f"Failed processing {name}: {e}")
            
    print(f"Total repositories updated and pushed: {updated_count}")

if __name__ == '__main__':
    update_repos()
