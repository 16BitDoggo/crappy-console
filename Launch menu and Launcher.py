import os
import sys
import subprocess
import pygame
import requests

# ---------------- SETTINGS -----------------
GITHUB_USER = "16BitDoggo"
GITHUB_REPO = "crappy-console-games"
BRANCH = "main"

DISC_PATH = "D:\\"   # Change this if you want local disc scanning
DOWNLOAD_DIR = "downloaded_exes"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/?ref={BRANCH}"

# ---------------- PYGAME SETUP -----------------
pygame.init()
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Launcher")

font = pygame.font.SysFont("Arial", 22)
clock = pygame.time.Clock()

# Controller setup
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Controller detected: {joystick.get_name()}")

CONTROLLER_COOLDOWN = 250  # ms
last_move_time = 0

# ---------------- ENTRY CLASS -----------------
class Entry:
    def __init__(self, name, pos, action, url=None, exe_path=None, image=None):
        self.name = name.replace(".exe", "")
        self.action = action
        self.url = url
        self.exe_path = exe_path
        self.image = image
        self.rect = pygame.Rect(pos[0], pos[1], 500, 80)

    def draw(self, surface, selected=False):
        color = (100, 180, 255) if selected else (60, 120, 200)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        if self.image:
            img = pygame.transform.scale(self.image, (70, 70))
            surface.blit(img, (self.rect.x - 80, self.rect.y + 5))
        label = font.render(self.name, True, (255, 255, 255))
        surface.blit(label, (self.rect.x + 10, self.rect.y + 25))

    def activate(self):
        if self.action == "github":
            download_and_run(self.url, self.name + ".exe")
        elif self.action == "disc":
            run_local_exe(self.exe_path)

# ---------------- FUNCTIONS -----------------
def fetch_exes_from_github():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        exe_files = [(item["name"], item["download_url"]) for item in data if item["name"].endswith(".exe")]
        pngs = {item["name"]: item["download_url"] for item in data if item["name"].endswith(".png")}
        return exe_files, pngs
    except Exception as e:
        print("Failed to fetch repo:", e)
        return [], {}

def find_exes_on_disc(path):
    exe_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".exe"):
                exe_files.append(os.path.join(root, file))
    return exe_files

def download_and_run(url, filename):
    local_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(local_path):
        print(f"Downloading {filename}...")
        r = requests.get(url)
        with open(local_path, "wb") as f:
            f.write(r.content)
    print(f"Launching {filename}...")
    subprocess.Popen(local_path, shell=True)

def run_local_exe(path):
    print(f"Launching {path}...")
    subprocess.Popen(path, shell=True)

def download_png(url, filename):
    local_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(local_path):
        r = requests.get(url)
        if r.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(r.content)
    if os.path.exists(local_path):
        try:
            return pygame.image.load(local_path).convert_alpha()
        except:
            return None
    return None

def load_local_png(path):
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert_alpha()
        except:
            return None
    return None

# ---------------- MAIN -----------------
mode = "github"
entries = []
selected_index = 0

def refresh_entries():
    global entries, selected_index
    entries = []
    y = 120
    if mode == "github":
        exe_files, pngs = fetch_exes_from_github()
        for name, url in exe_files:
            image = None
            png_name = name.replace(".exe", ".png")
            if png_name in pngs:
                image = download_png(pngs[png_name], png_name)
            entries.append(Entry(name, (150, y), "github", url=url, image=image))
            y += 100
    else:
        exe_files = find_exes_on_disc(DISC_PATH)
        for exe in exe_files:
            png_path = exe[:-4] + ".png"
            image = load_local_png(png_path)
            entries.append(Entry(os.path.basename(exe), (150, y), "disc", exe_path=exe, image=image))
            y += 100
    selected_index = 0 if entries else -1

refresh_entries()

running = True
while running:
    screen.fill((30, 30, 30))
    label = font.render(
        f"Mode: {mode.upper()} - Use Arrows/D-Pad, A/Enter=Launch, Start/Tab=Switch",
        True, (255, 255, 255))
    screen.blit(label, (50, 10))

    for i, entry in enumerate(entries):
        entry.draw(screen, selected=(i == selected_index))

    # ---------------- CONTROLLER POLLING -----------------
    current_time = pygame.time.get_ticks()
    if joystick:
        # D-Pad / hat movement
        hat_x, hat_y = joystick.get_hat(0)
        if hat_y == 1 and current_time - last_move_time > CONTROLLER_COOLDOWN:
            selected_index = (selected_index - 1) % len(entries)
            last_move_time = current_time
        elif hat_y == -1 and current_time - last_move_time > CONTROLLER_COOLDOWN:
            selected_index = (selected_index + 1) % len(entries)
            last_move_time = current_time

        # Buttons
        if joystick.get_button(0):  # A
            if 0 <= selected_index < len(entries):
                entries[selected_index].activate()
                pygame.time.wait(150)
        if joystick.get_button(7):  # Start
            mode = "disc" if mode == "github" else "github"
            refresh_entries()
            pygame.time.wait(150)

    # ---------------- KEYBOARD / MOUSE -----------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_DOWN, pygame.K_s]:
                selected_index = (selected_index + 1) % len(entries)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                selected_index = (selected_index - 1) % len(entries)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                if 0 <= selected_index < len(entries):
                    entries[selected_index].activate()
            elif event.key == pygame.K_TAB:
                mode = "disc" if mode == "github" else "github"
                refresh_entries()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, entry in enumerate(entries):
                if entry.rect.collidepoint(event.pos):
                    entry.activate()

    pygame.display.flip()
    clock.tick(30)
