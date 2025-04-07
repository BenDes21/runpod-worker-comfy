import subprocess
import os
import sys # Import sys to potentially check executable path if needed later
import json
import uuid
import time
from rp_logging import log

# --- AJOUT : Définir les chemins essentiels ---
# Ces chemins DOIVENT correspondre à ceux utilisés dans votre Dockerfile
COMFYUI_PATH = "/opt/ComfyUI"
VENV_PYTHON = "/opt/ComfyUI/venv/bin/python3"
HANDLER_TMP_PATH = "/tmp/rp-handler-tmp" # Ou tout autre chemin temporaire que vous utilisez

# Assurez-vous que le répertoire temporaire existe (si utilisé)
# os.makedirs(HANDLER_TMP_PATH, exist_ok=True) # Décommentez si vous utilisez des fichiers temporaires

# ... (Le reste de vos imports et configurations initiales) ...

def run_comfyui(job):
    """
    Starts ComfyUI as a subprocess and executes the job workflow.
    (Fonction adaptée pour la modification minimale)
    """
    job_id = job.get("id", str(uuid.uuid4()))
    job_input = job.get("input", {})
    workflow = job_input.get("workflow", None) # Ou 'api_workflow' selon votre schéma

    if not workflow:
        return {"error": "No workflow (or api_workflow) provided in input"}

    # --- MODIFICATION MINIMALE : Construction de la commande ---
    # Adaptez les arguments passés à main.py selon le besoin de votre ComfyUI/handler
    # L'important est d'utiliser VENV_PYTHON
    # NOTE: Assurez-vous que votre main.py (ou un script wrapper) gère la réception du workflow
    #       (par exemple via un fichier, stdin, ou autre méthode).
    #       Cette version minimale suppose que main.py sait quoi faire quand il est lancé.
    #       Si vous utilisiez des fichiers temporaires, remettez cette logique ici.
    command = [
        VENV_PYTHON,                     # <--- Utilise le Python du venv
        "main.py"                        # Lance le script principal de ComfyUI
        # --- Ajoutez ICI les arguments que votre ComfyUI attend ---
        # Par exemple :
        # "--output-directory", "/path/to/outputs",
        # "--disable-metadata",
        # "--preview-method", "none", # Utile en serverless
        # "--port", "8188", # Généralement pas nécessaire car on ne s'y connecte pas directement
        # ... autres flags nécessaires ...
    ]

    log(f"[{job_id}] Using Python executable: {VENV_PYTHON}")
    log(f"[{job_id}] Attempting to execute command: {' '.join(command)} in CWD: {COMFYUI_PATH}")

    process = None
    try:
        # --- MODIFICATION MINIMALE : Exécution avec le bon CWD ---
        process = subprocess.Popen(
            command,
            # stdout=subprocess.PIPE, # Gardez ou commentez selon votre besoin de logs
            # stderr=subprocess.PIPE, # Gardez ou commentez selon votre besoin de logs
            cwd=COMFYUI_PATH,       # <--- S'assure que ComfyUI est lancé depuis son propre répertoire
            text=True,              # Décode stdout/stderr si vous les capturez
            # env=os.environ.copy() # Peut être nécessaire si des variables d'env doivent être passées
        )

        log(f"[{job_id}] ComfyUI process likely started (PID: {process.pid})")

        # --- LOGIQUE D'ATTENTE ET DE RÉSULTAT ---
        # ATTENTION : Cette partie dépend FORTEMENT de comment votre ComfyUI
        # communique la fin de l'exécution (fichier de statut, sortie standard, etc.)
        # Remplacez cette section par la logique d'attente / de récupération de résultat
        # qui était présente dans votre rp_handler.py original ou qui est nécessaire.
        # Exemple très basique (NE PAS UTILISER EN PRODUCTION SANS ADAPTATION):
        try:
            # stdout, stderr = process.communicate(timeout=300) # Attente simple avec timeout
            # log(f"[{job_id}] ComfyUI stdout:\n{stdout}")
            # log(f"[{job_id}] ComfyUI stderr:\n{stderr}")
            # if process.returncode != 0:
            #     return {"error": f"ComfyUI process exited with code {process.returncode}. Check worker logs."}
            # else:
                 # ICI: Logique pour trouver/lire le résultat (image, etc.)
                 # Ceci est juste un placeholder
            #    return {"message": "ComfyUI process finished (result retrieval logic needed)"}

             # SIMULATION : Si vous attendez un fichier status/output comme dans l'exemple précédent
             # Remettez ici la boucle d'attente du fichier status_file_path, la lecture, etc.
             # C'est probablement nécessaire pour un fonctionnement fiable.
             # Pour l'instant, on simule une attente simple pour le process.
             process.wait(timeout=300) # Attendre max 5 minutes que le process se termine
             if process.returncode == 0:
                 log(f"[{job_id}] ComfyUI process finished successfully (exit 0).")
                 # !!! ICI : Vous devez implémenter la récupération du résultat réel !!!
                 # Par exemple, lire un fichier de sortie prédéfini, trouver l'image générée, etc.
                 return {"output": {"message": "Job completed (placeholder result). Check volume/logs for actual output."}}
             else:
                 log(f"[{job_id}] ComfyUI process failed with exit code {process.returncode}.", level="ERROR")
                 # Essayez de récupérer stderr si vous l'avez pipé
                 # stderr_output = process.stderr.read() if process.stderr else "stderr not captured"
                 # log(f"[{job_id}] ComfyUI stderr: {stderr_output}", level="ERROR")
                 return {"error": f"ComfyUI failed with exit code {process.returncode}."}


        except subprocess.TimeoutExpired:
            log(f"[{job_id}] ComfyUI process timed out.", level="ERROR")
            process.kill()
            # stdout, stderr = process.communicate() # Récupérer ce qui a été écrit avant le kill
            return {"error": "ComfyUI process timed out"}
        # --- FIN DE LA LOGIQUE D'ATTENTE (À ADAPTER) ---

    except FileNotFoundError:
         log(f"[{job_id}] Error: Command not found. Is '{VENV_PYTHON}' or 'main.py' correct?", level="CRITICAL")
         return {"error": f"Failed to find executable '{VENV_PYTHON}' or script 'main.py'"}
    except Exception as e:
        log(f"[{job_id}] Error running ComfyUI process: {e}", level="ERROR")
        if process and process.poll() is None:
             process.kill()
        return {"error": f"Failed to execute ComfyUI: {e}"}

    # finally:
        # Remettez ici votre logique de nettoyage de fichiers temporaires si nécessaire


def handler(job):
    """ The main handler function called by RunPod serverless. """
    log(f"Processing job ID: {job.get('id')}")
    try:
        # --- Validation d'entrée (gardez votre logique existante si vous en avez une) ---
        # ...

        result = run_comfyui(job)

    except Exception as e:
        log(f"Handler error: {e}", level="ERROR")
        # Peut-être masquer les détails de l'erreur pour l'utilisateur final
        return {"error": "An unexpected error occurred in the handler."}

    log(f"Job {job.get('id')} finished.")
    return result


# Start the RunPod worker
if __name__ == "__main__":
    log("Starting RunPod ComfyUI Worker (minimal change version)...")
    # S'assurer que CWD est correct même pour le handler lui-même (normalement géré par RunPod)
    # log(f"Handler current working directory: {os.getcwd()}")
    import runpod
    runpod.serverless.start({"handler": handler})
