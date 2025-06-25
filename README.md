# python flask app for master thesis app

Backend for Next JS 15 app

## 🖥️ Wymagania wstępne (Windows)

Aby uruchomić aplikację Flask w środowisku VS Code na systemie Windows, potrzebujesz:

### Zainstalowane oprogramowanie:

1. **Python** (zalecana wersja 3.12)  
   Pobierz: https://www.python.org/downloads/  
   Podczas instalacji zaznacz opcję `Add Python to PATH`.

2. **Anaconda lub Miniconda**

   - Anaconda: https://www.anaconda.com/products/distribution
   - Miniconda (lżejsza): https://docs.conda.io/en/latest/miniconda.html

3. **Visual Studio Code**  
   Pobierz: https://code.visualstudio.com/

4. **Rozszerzenia VS Code (Extensions)**:
   - Python (by Microsoft)
   - Pylance
   - Jupyter (opcjonalnie)

---

Opcja 1 - Aby stworzyć środowisko wirtualne (Conda):

```bash
conda env create -f environment.yml
```

Uruchomienie środowiska wirtualnego conda:

```bash
conda activate env_name
```

Opcja 2 - Aby stworzyć środowisko wirtualne (Python):

```bash
python -m venv venv
```

# CMD:

```bash
venv\Scripts\activate
```

# PowerShell

```bash
.\venv\Scripts\Activate.ps1
```

Instalacja wymaganych pakietów:

```bash
pip install -r requirements.txt
```

Uruchominie aplikacji flask - lokalnie:

```bash
flask run
```

Zmienne środowiskowe:

W folderze głównym swtórz plik ".env"

Wymagana zmienna:

```bash
MONGODB_URI="mongodb://localhost:27017/nazwa_bazy"                      # LUB adres bazy danych z mongo atlas
```
