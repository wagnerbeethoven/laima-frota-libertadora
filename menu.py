import pygame
import sys
import pyttsx3  # Biblioteca para síntese de voz
import subprocess
import os  # Para verificar se o arquivo existe
import time  # Para simular o tempo de carregamento

class Menu:
    def __init__(self):
        pygame.init()
        self.engine = pyttsx3.init()  # Inicializa o sintetizador de voz
        self.engine.setProperty("rate", 300)  # Define a velocidade da fala
        self.screen = pygame.display.set_mode((800, 600))  # Define o tamanho da janela
        pygame.display.set_caption("Frota Libertadora")
        self.font = pygame.font.Font(None, 36)  # Fonte padrão
        self.in_main_menu = True
        self.in_submenu = False
        self.menu_selected = 0
        self.first_announcement_done = False  # Controla a fala inicial
        self.menu_options = [
            "Iniciar Jogo",
            "Aprender o Jogo",
            "Sair",
        ]
        self.submenu_options = [
            "Aprender Teclas do Jogo",
            "Conhecer Termos e Conceitos",
            "Regras Detalhadas",
            "Voltar",
        ]
        self.text_color = (255, 255, 255)  # Cor do texto (branco)
        self.background_color = (20, 20, 20)  # Cor de fundo (cinza escuro)
        self.title_color = (255, 215, 0)  # Cor do título (dourado)
        self.highlight_color = (50, 205, 50)  # Cor de destaque (verde)
        self.border_color = (255, 255, 255)  # Cor da borda do menu (branco)

    def announce(self, message):
        """Fala a mensagem em voz alta."""
        self.engine.say(message)
        self.engine.runAndWait()

    def handle_main_menu_selection(self):
        """Trata a opção selecionada no menu principal."""
        selected_option = self.menu_options[self.menu_selected]
        if selected_option == "Iniciar Jogo":
            self.announce("Transportando para zona de guerra")
            self.start_new_game()
        elif selected_option == "Aprender o Jogo":
            self.in_main_menu = False
            self.in_submenu = True
            self.menu_selected = 0  # Reset para o submenu
            self.announce(self.submenu_options[self.menu_selected])  # Anuncia a primeira opção do submenu
        elif selected_option == "Sair":
            self.exit_game()

    def handle_submenu_selection(self):
        """Trata a opção selecionada no submenu."""
        selected_option = self.submenu_options[self.menu_selected]
        if selected_option == "Aprender Teclas do Jogo":
            self.show_controls_info()
        elif selected_option == "Conhecer Termos e Conceitos":
            self.show_terms_info()
        elif selected_option == "Regras Detalhadas":
            self.show_detailed_rules()
        elif selected_option == "Voltar":
            self.announce("Voltando ao menu principal...")

            # Fecha a janela atual e reabre o menu principal
            pygame.quit()

            # Executa o script menu.py novamente
            menu_file = "menu.py"
            if os.path.exists(menu_file):
                try:
                    subprocess.run(["python", menu_file])
                except Exception as e:
                    print(f"Erro ao executar {menu_file}: {e}")
                    sys.exit()
            else:
                print(f"Arquivo {menu_file} não encontrado.")
                sys.exit()

    def exit_game(self):
        """Fecha o jogo."""
        pygame.quit()
        sys.exit()

    def start_new_game(self):
        """Inicia um novo jogo."""

        # Fecha a janela atual antes de iniciar o próximo script
        pygame.quit()

        # Verifica se o arquivo do jogo principal existe
        if os.path.exists("frota_libertadora.py"):
            try:
                subprocess.run(["python", "frota_libertadora.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao executar frota_libertadora.py: {e}")
                self.announce("Erro ao iniciar o jogo.")
                sys.exit()
        else:
            print("Erro: Arquivo frota_libertadora.py não encontrado.")
            self.announce("Arquivo frota_libertadora.py não encontrado.")
            sys.exit()

    
    def show_controls_info(self):
        """Exibe informações sobre os controles."""
        self.announce("Exibindo informações sobre os controles do jogo...")

    def show_terms_info(self):
        """Exibe informações sobre termos e conceitos."""
        self.announce("Exibindo informações sobre termos e conceitos...")

    def show_detailed_rules(self):
        """Exibe as regras detalhadas."""
        self.announce("Exibindo as regras detalhadas do jogo...")

    def draw_menu(self, options):
        """Desenha o menu na tela, incluindo o título."""
        self.screen.fill(self.background_color)  # Preenche a tela com a cor de fundo
        self.option_rects = []  # Armazena as áreas de clique para cada opção

        # Desenha o título na parte superior
        title_font = pygame.font.Font(None, 48)  # Fonte maior para o título
        title_surface = title_font.render("Frota Libertadora", True, self.title_color)  # Cor do título
        title_x = (self.screen.get_width() - title_surface.get_width()) // 2
        title_y = 50  # Espaço no topo para o título
        self.screen.blit(title_surface, (title_x, title_y))

        # Desenha um retângulo de borda ao redor do menu
        menu_border_rect = pygame.Rect((self.screen.get_width() - 400) // 2, 130, 400, 250)
        pygame.draw.rect(self.screen, self.border_color, menu_border_rect, 3)

        # Desenha as opções do menu
        for i, option in enumerate(options):
            color = self.text_color
            if i == self.menu_selected:  # Destaca a opção selecionada
                color = self.highlight_color  # Verde para a opção selecionada
            text_surface = self.font.render(option, True, color)
            x = (self.screen.get_width() - text_surface.get_width()) // 2
            y = 160 + i * 40  # Posiciona os itens do menu verticalmente
            rect = text_surface.get_rect(topleft=(x, y))
            self.option_rects.append(rect)  # Armazena a área de clique
            self.screen.blit(text_surface, rect.topleft)

        pygame.display.flip()  # Atualiza a tela

    def menu_loop(self):
        """Loop principal do menu."""
        # Fala o título ao iniciar o menu
        if not self.first_announcement_done:
            self.announce("Bem-vindo ao jogo Frota Libertadora!")
            self.announce(f"{self.menu_options[self.menu_selected]}")
            self.first_announcement_done = True

        while self.in_main_menu or self.in_submenu:
            options = (
                self.menu_options if self.in_main_menu else self.submenu_options
            )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_game()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.menu_selected = (self.menu_selected - 1) % len(options)
                        self.announce(options[self.menu_selected])
                    elif event.key == pygame.K_DOWN:
                        self.menu_selected = (self.menu_selected + 1) % len(options)
                        self.announce(options[self.menu_selected])
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_RIGHT:
                        if self.in_main_menu:
                            self.handle_main_menu_selection()
                        elif self.in_submenu:
                            self.handle_submenu_selection()
                    elif event.key == pygame.K_ESCAPE:
                        if self.in_submenu:
                            self.announce("Voltando ao menu principal.")
                            self.in_submenu = False
                            self.in_main_menu = True
                            self.menu_selected = 0
                            self.first_announcement_done = False
                        else:
                            self.exit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clique com o botão esquerdo
                        for i, rect in enumerate(self.option_rects):
                            if rect.collidepoint(event.pos):
                                self.menu_selected = i
                                self.announce(options[self.menu_selected])
                                if self.in_main_menu:
                                    self.handle_main_menu_selection()
                                elif self.in_submenu:
                                    self.handle_submenu_selection()
            self.draw_menu(options)

    def get_player_name(self):
        self.announce('Digite seu nome ou pressione Enter para jogar no modo Anônimo.')
        name_input = ''
        input_active = True
        font = pygame.font.Font(None, 36)  # Fonte para renderizar o texto
        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_game()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.player_name = name_input.strip() if name_input.strip() else 'Dragonian'
                        greeting = f'Olá, Comandante {self.player_name}, na próxima tela, pressione f para silenciar a fala. Pressione f novamente para reativá-la.'
                        self.announce(greeting)
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        name_input = name_input[:-1]
                    else:
                        if event.unicode.isalnum() or event.unicode.isspace():
                            name_input += event.unicode
            self.screen.fill((0, 0, 0))  # Limpa a tela
            prompt_surface = font.render('Digite seu nome: ' + name_input, True, (255, 255, 255))
            self.screen.blit(prompt_surface, (50, 300))  # Posiciona o texto
            pygame.display.flip()  # Atualiza a tela


# Execução do programa
if __name__ == "__main__":
    menu = Menu()
    menu.menu_loop()
