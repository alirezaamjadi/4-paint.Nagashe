import pygame
import sys
import json

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1000, 700
COLOR_BG = (64, 224, 208)  # فیروزه‌ای روشن
FPS = 60

# فونت‌های کوچک‌تر
FONT = pygame.font.SysFont("Arial", 20)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_LARGE = pygame.font.SysFont("Arial", 36, bold=True)

def load_notebook(path="notebook.json"):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("notes", "")
    except FileNotFoundError:
        return ""

def save_notebook(text, path="notebook.json"):
    with open(path, "w") as f:
        json.dump({"notes": text}, f)

class Button:
    def __init__(self, rect, text, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.bg_color = (255, 255, 255)
        self.text_color = (139, 0, 0)  # قرمز تیره
        self.border_color = (0, 0, 0)

    def draw(self, surf):
        pygame.draw.rect(surf, self.bg_color, self.rect, border_radius=10)
        pygame.draw.rect(surf, self.border_color, self.rect, 2, border_radius=10)
        txt_surf = FONT_SMALL.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surf.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

class SetupScreen:
    def __init__(self):
        self.input_boxes = {
            'team1_name': '',
            'team1_player1': '',
            'team1_player2': '',
            'team2_name': '',
            'team2_player1': '',
            'team2_player2': '',
            'final_score': '5',
        }
        self.fullscreen = False
        self.done = False
        self.selected_input = None

    def run(self):
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        clock = pygame.time.Clock()
        while not self.done:
            screen.fill(COLOR_BG)
            y = 50
            for key in self.input_boxes:
                label = FONT.render(key.replace('_', ' ').title(), True, (0, 0, 0))
                screen.blit(label, (50, y))
                box_rect = pygame.Rect(300, y, 200, 30)
                pygame.draw.rect(screen, (255,255,255), box_rect, border_radius=6)
                text = FONT.render(self.input_boxes[key], True, (0,0,0))
                screen.blit(text, (305, y + 5))
                if self.selected_input == key:
                    pygame.draw.rect(screen, (255, 0, 0), box_rect, 2, border_radius=6)
                y += 50

            toggle_btn_rect = pygame.Rect(300, y + 20, 200, 40)
            pygame.draw.rect(screen, (64, 224, 208), toggle_btn_rect, border_radius=10)
            pygame.draw.rect(screen, (0, 0, 0), toggle_btn_rect, 2, border_radius=10)
            fs_text = "Switch to Fullscreen" if not self.fullscreen else "Switch to Windowed"
            screen.blit(FONT.render(fs_text, True, (139, 0, 0)), (310, y + 30))

            start_btn = pygame.Rect(400, y + 80, 200, 50)
            pygame.draw.rect(screen, (178, 34, 34), start_btn, border_radius=10)
            screen.blit(FONT.render("Start Game", True, (255,255,255)), (420, y + 90))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if toggle_btn_rect.collidepoint(event.pos):
                        self.fullscreen = not self.fullscreen
                    elif start_btn.collidepoint(event.pos):
                        self.done = True
                    else:
                        y_check = 50
                        clicked = False
                        for key in self.input_boxes:
                            rect = pygame.Rect(300, y_check, 200, 30)
                            if rect.collidepoint(event.pos):
                                self.selected_input = key
                                clicked = True
                                break
                            y_check += 50
                        if not clicked:
                            self.selected_input = None
                elif event.type == pygame.KEYDOWN and self.selected_input:
                    if event.key == pygame.K_BACKSPACE:
                        self.input_boxes[self.selected_input] = self.input_boxes[self.selected_input][:-1]
                    elif event.key == pygame.K_RETURN:
                        self.selected_input = None
                    else:
                        if event.unicode.isprintable():
                            self.input_boxes[self.selected_input] += event.unicode

            pygame.display.flip()
            clock.tick(FPS)

        return self.input_boxes, self.fullscreen

class GameScreen:
    def __init__(self, team_info, fullscreen):
        self.team_info = team_info
        self.fullscreen = fullscreen
        self.final_score = int(team_info.get("final_score", 5))
        self.score = {team_info['team1_name']: 0, team_info['team2_name']: 0}
        self.notes = load_notebook()
        self.show_notebook = False
        self.notebook_active = False
        self.notebook_rect = pygame.Rect(50, 50, 700, 200)
        self.drawing = False
        self.brush_color = (0, 0, 0)
        self.eraser_mode = False
        self.canvas = pygame.Surface((700, 500))
        self.canvas.fill((255, 255, 255))
        self.winner = None  # ذخیره نام تیم برنده

        self.color_palette = [
            (255, 0, 0), (0, 0, 0), (255, 255, 255), (64, 224, 208), (0, 128, 128),
            (178, 34, 34), (220, 20, 60), (105, 105, 105), (255, 182, 193), (47, 79, 79),
            (240, 248, 255), (250, 250, 250), (0, 255, 255), (0, 139, 139), (139, 0, 0),
            (255, 165, 0), (255, 215, 0), (124, 252, 0), (0, 255, 127), (0, 0, 139),
            (138, 43, 226), (255, 20, 147), (0, 191, 255), (255, 105, 180), (210, 105, 30),
        ]

        self.buttons = [
            Button((800, 50, 120, 30), "+1 " + team_info['team1_name'], lambda: self.change_score(team_info['team1_name'], 1)),
            Button((800, 90, 120, 30), "-1 " + team_info['team1_name'], lambda: self.change_score(team_info['team1_name'], -1)),
            Button((800, 130, 120, 30), "+1 " + team_info['team2_name'], lambda: self.change_score(team_info['team2_name'], 1)),
            Button((800, 170, 120, 30), "-1 " + team_info['team2_name'], lambda: self.change_score(team_info['team2_name'], -1)),
            Button((800, 220, 120, 30), "Notebook", self.toggle_notebook),
            Button((800, 260, 120, 30), "Eraser", self.toggle_eraser),
            Button((800, 300, 120, 30), "Clear All", self.clear_canvas),
        ]

        flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Team Drawing Game")

    def change_score(self, team, delta):
        if self.winner is not None:
            return  # اگر بازی تمام شده، تغییر امتیاز نده

        self.score[team] = max(0, self.score[team] + delta)
        if self.score[team] >= self.final_score:
            self.winner = team  # تیم برنده را ثبت کن

    def toggle_notebook(self):
        self.show_notebook = not self.show_notebook
        self.notebook_active = self.show_notebook

    def toggle_eraser(self):
        self.eraser_mode = not self.eraser_mode
        self.brush_color = (255, 255, 255) if self.eraser_mode else (0, 0, 0)

    def clear_canvas(self):
        self.canvas.fill((255, 255, 255))

    def draw_palette(self):
        x = 50
        y = 570
        size = 30
        for color in self.color_palette:
            rect = pygame.Rect(x, y, size, size)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            if color == self.brush_color and not self.eraser_mode:
                pygame.draw.rect(self.screen, (255, 0, 0), rect, 3)
            x += size + 10

    def handle_events(self, event):
        if self.winner is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # بعد از پایان بازی، با ESC خروج
                pygame.quit()
                sys.exit()
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.notebook_active and self.notebook_rect.collidepoint(event.pos):
                self.notebook_active = True
            elif event.pos[1] < 570:
                self.drawing = True
            else:
                x = 50
                y = 570
                size = 30
                for color in self.color_palette:
                    rect = pygame.Rect(x, y, size, size)
                    if rect.collidepoint(event.pos):
                        self.brush_color = color
                        self.eraser_mode = False
                        break
                    x += size + 10
        elif event.type == pygame.MOUSEBUTTONUP:
            self.drawing = False
        elif event.type == pygame.MOUSEMOTION and self.drawing:
            if 50 <= event.pos[0] <= 750 and 50 <= event.pos[1] <= 550:
                pygame.draw.circle(self.canvas, self.brush_color, (event.pos[0]-50, event.pos[1]-50), 8)

        for btn in self.buttons:
            btn.handle_event(event)

        if self.notebook_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.notes = self.notes[:-1]
            elif event.key == pygame.K_RETURN:
                self.notes += '\n'
            elif event.key == pygame.K_ESCAPE:
                self.notebook_active = False
            else:
                if event.unicode.isprintable():
                    self.notes += event.unicode

    def draw_scores(self):
        y = 10
        for team, score in self.score.items():
            text_surface = FONT_LARGE.render(f"{team}: {score}", True, (139, 0, 0))
            bg_rect = text_surface.get_rect(topleft=(20, y))
            pygame.draw.rect(self.screen, (255, 255, 255), bg_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, 2)
            self.screen.blit(text_surface, (20, y))
            y += 50

    def draw_notebook(self):
        pygame.draw.rect(self.screen, (255, 255, 255), self.notebook_rect, border_radius=10)
        pygame.draw.rect(self.screen, (0, 0, 0), self.notebook_rect, 3, border_radius=10)

        lines = self.notes.split('\n')
        y = self.notebook_rect.y + 10
        max_lines = 10
        for line in lines[-max_lines:]:
            txt = FONT_SMALL.render(line, True, (139, 0, 0))
            self.screen.blit(txt, (self.notebook_rect.x + 10, y))
            y += 18

        if self.notebook_active:
            cursor_x = self.notebook_rect.x + 10 + FONT_SMALL.size(lines[-1] if lines else '')[0]
            cursor_y = y - 18
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.line(self.screen, (139, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 16), 2)

    def draw_footer(self):
        footer_text = FONT_SMALL.render("Builder Game : alirezaamjadi", True, (139, 0, 0))
        self.screen.blit(footer_text, (WIDTH - footer_text.get_width() - 20, HEIGHT - 30))

    def draw_winner_screen(self):
        self.screen.fill(COLOR_BG)
        winner = self.winner
        info = self.team_info

        pygame.draw.rect(self.screen, (255, 255, 255), (150, 100, 700, 400), border_radius=15)
        pygame.draw.rect(self.screen, (139, 0, 0), (150, 100, 700, 400), 5, border_radius=15)

        title = FONT_LARGE.render("Game Champion:", True, (178, 34, 34))
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 120))

        team_name = winner
        team_text = FONT.render(f"Team Name: {team_name}", True, (0,0,0))
        self.screen.blit(team_text, (200, 200))

        if team_name == info['team1_name']:
            players = [info['team1_player1'], info['team1_player2']]
        else:
            players = [info['team2_player1'], info['team2_player2']]
        players_text = FONT.render(f"Players: {players[0]} and {players[1]}", True, (0,0,0))
        self.screen.blit(players_text, (200, 250))

        score_text = FONT.render(f"Final Score: {self.score[winner]}", True, (0,0,0))
        self.screen.blit(score_text, (200, 300))

        info_text = FONT_SMALL.render("Press ESC to exit.", True, (139, 0, 0))
        self.screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 400))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_events(event)

            if self.winner:
                self.draw_winner_screen()
            else:
                self.screen.fill(COLOR_BG)
                self.screen.blit(self.canvas, (50, 50))
                self.draw_palette()
                for btn in self.buttons:
                    btn.draw(self.screen)
                self.draw_scores()
                if self.show_notebook:
                    self.draw_notebook()
                self.draw_footer()

            pygame.display.flip()
            clock.tick(FPS)

        save_notebook(self.notes)
        pygame.quit()
        sys.exit()

def main():
    setup = SetupScreen()
    team_info, fullscreen = setup.run()
    game = GameScreen(team_info, fullscreen)
    game.run()

if __name__ == "__main__":
    main()
