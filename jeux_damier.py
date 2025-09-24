import tkinter as tk
import platform

class Damier(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config(bg="chocolate")
        self.title("MON SIMPLE DAMIER")
        
        # Récupération des dimensions de l'écran
        self.w, self.h = self.winfo_screenwidth(), self.winfo_screenheight()
        
        # Gestion du plein écran selon l'OS
        if platform.system() == "Windows":
            self.geometry(f"{self.w}x{self.h}+0+0")
            self.state('zoomed')
        elif platform.system() == "Darwin":  # macOS
            self.geometry(f"{self.w}x{self.h}+0+0")
            self.state('zoomed')
        else:  # Linux
            self.geometry(f"{self.w}x{self.h}+0+0")
            self.attributes('-zoomed', True)  # Alternative pour Linux
        
        # Dimensions adaptatives du plateau
        self.lo = min(self.w * 0.7, self.h * 0.9)
        self.la = self.lo * 0.75
        
        self.click = False
        self.pion_selected = None
        self.pion_selec_coord = None
        self.pion = {}
        self.cases = {}
        self.pions_captures = {"coral": 0, "cadetblue": 0}
        self.rois = {}
        self.tour_joueur = "coral"
        
        # Création du conteneur principal pour centrer le damier
        self.main_frame = tk.Frame(self, bg="chocolate")
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Frame pour le joueur 1 (gauche)
        self.player1_frame = tk.Frame(self.main_frame, bg="chocolate", width=self.w*0.15)
        self.player1_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Frame pour le damier (centre)
        self.board_frame = tk.Frame(self.main_frame, bg="chocolate")
        self.board_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=20)
        
        # Frame pour le joueur 2 (droite)
        self.player2_frame = tk.Frame(self.main_frame, bg="chocolate", width=self.w*0.15)
        self.player2_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        self.create_board()
        self.chequer_bank()
        self.create_pieces()

        # Bindings souris sur le canvas
        self.can.bind("<Button-1>", lambda event: self.move_chequer(event))
        self.can.bind("<B1-Motion>", lambda event: self.movep(event))
        self.can.bind("<ButtonRelease-1>", lambda event: self.bring(event))
        
        # Bind pour le redimensionnement
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        """Redimensionnement adaptatif lorsque la fenêtre change de taille"""
        if event.widget == self:
            new_w = event.width
            new_h = event.height
            
            # Recalcul des dimensions du damier
            self.lo = min(new_w * 0.6, new_h * 0.8)
            self.la = self.lo * 0.75
            
            # Redimensionner le canvas
            self.can.config(width=self.lo, height=self.la)
            
            # Redessiner le damier et les pions
            self.redraw_board()

    def redraw_board(self):
        """Redessine tout le damier avec les nouvelles dimensions"""
        # Supprimer tous les éléments existants
        self.can.delete("all")
        self.pion.clear()
        self.cases.clear()
        if hasattr(self, 'crowns'):
            self.crowns.clear()
        
        # Recréer le damier et les pions
        self.create_board()
        self.create_pieces()

    def create_board(self):
        """Création d'un damier 10x10 avec dimensions adaptatives"""
        # Créer le canvas s'il n'existe pas encore
        if not hasattr(self, 'can'):
            self.can = tk.Canvas(self.board_frame, width=self.lo, height=self.la, 
                                bg="burlywood", bd=3, relief="groove")
            self.can.pack(expand=True, pady=20)
        
        cell_width = self.lo / 10
        cell_height = self.la / 10
        
        for row in range(10):
            for col in range(10):
                color = "brown" if (row + col) % 2 == 1 else "burlywood"
                x0 = col * cell_width
                y0 = row * cell_height
                x1 = (col + 1) * cell_width
                y1 = (row + 1) * cell_height
                
                self.cases[(row, col)] = self.can.create_rectangle(
                    x0, y0, x1, y1,
                    fill=color, outline="black", width=1
                )

    def create_pieces(self):
        """Placement initial des pions avec dimensions adaptatives"""
        cell_width = self.lo / 10
        cell_height = self.la / 10
        margin = min(cell_width, cell_height) * 0.2
        
        # Joueur 1 : lignes 0 à 3
        for row in range(0, 4):
            for col in range(10):
                if (row + col) % 2 == 1:
                    x0 = col * cell_width + margin
                    y0 = row * cell_height + margin
                    x1 = (col + 1) * cell_width - margin
                    y1 = (row + 1) * cell_height - margin
                    
                    piece_id = self.can.create_oval(
                        x0, y0, x1, y1,
                        fill="coral", outline="black", width=2
                    )
                    self.pion[(row, col)] = piece_id
        
        # Joueur 2 : lignes 6 à 9
        for row in range(6, 10):
            for col in range(10):
                if (row + col) % 2 == 1:
                    x0 = col * cell_width + margin
                    y0 = row * cell_height + margin
                    x1 = (col + 1) * cell_width - margin
                    y1 = (row + 1) * cell_height - margin
                    
                    piece_id = self.can.create_oval(
                        x0, y0, x1, y1,
                        fill="cadetblue", outline="black", width=2
                    )
                    self.pion[(row, col)] = piece_id

    def chequer_bank(self):
        """Création des zones pour les pièces capturées avec dimensions adaptatives"""
        bank_width = self.w * 0.12
        bank_height = self.h * 0.6
        
        # Zone joueur 1 (gauche)
        self.can_bank1 = tk.Canvas(self.player1_frame, width=bank_width, height=bank_height,
                                  bg="maroon", bd=3, relief="groove")
        self.can_bank1.pack(pady=20)
        
        # Labels joueur 1
        tk.Label(self.player1_frame, text="PLAYER 1", font=("Arial", self.get_font_size(20)), 
                bg="chocolate", fg="white").pack(pady=5)
        tk.Label(self.player1_frame, text="SCORE P1", font=("Arial", self.get_font_size(16)),
                bg="red", fg="white").pack(pady=5)
        
        self.score_p1 = tk.StringVar(value="0")
        self.label_score_p1 = tk.Label(self.player1_frame, textvariable=self.score_p1,
                                      font=("Georgia", self.get_font_size(18)), 
                                      bg="white", width=8, relief="sunken")
        self.label_score_p1.pack(pady=5)
        
        # Zone joueur 2 (droite)
        self.can_bank2 = tk.Canvas(self.player2_frame, width=bank_width, height=bank_height,
                                  bg="maroon", bd=3, relief="groove")
        self.can_bank2.pack(pady=20)
        
        # Labels joueur 2
        tk.Label(self.player2_frame, text="PLAYER 2", font=("Arial", self.get_font_size(20)),
                bg="chocolate", fg="white").pack(pady=5)
        tk.Label(self.player2_frame, text="SCORE P2", font=("Arial", self.get_font_size(16)),
                bg="red", fg="white").pack(pady=5)
        
        self.score_p2 = tk.StringVar(value="0")
        self.label_score_p2 = tk.Label(self.player2_frame, textvariable=self.score_p2,
                                      font=("Georgia", self.get_font_size(18)),
                                      bg="white", width=8, relief="sunken")
        self.label_score_p2.pack(pady=5)

    def get_font_size(self, base_size):
        """Calcule la taille de police adaptative"""
        return max(base_size, int(min(self.w, self.h) / 80))

    def move_chequer(self, event):
        """Lors d'un clic, on détermine si l'on clique sur un pion."""
        x, y = event.x, event.y
        
        for position, piece_id in self.pion.items():
            coords = self.can.coords(piece_id)
            if coords and len(coords) == 4:
                if coords[0] < x < coords[2] and coords[1] < y < coords[3]:
                    color = self.can.itemcget(piece_id, "fill")
                    if color == self.tour_joueur:
                        self.pion_selected = position
                        self.pion_selec_coord = coords
                        self.click = True
                        break

    def movep(self, event):
        """Déplacement temporaire du pion avec la souris."""
        if self.click and self.pion_selected:
            x1, y1 = event.x, event.y
            piece_id = self.pion[self.pion_selected]
            # Taille proportionnelle pour le drag
            size = min(self.lo, self.la) / 30
            self.can.coords(piece_id, 
                           x1 - size, y1 - size, 
                           x1 + size, y1 + size)

    def bring(self, event):
        """Validation du déplacement lors du relâchement."""
        if not self.pion_selected:
            return

        orig = self.pion_selected
        target = self.get_board_coords(event.x, event.y)
        
        # Vérifier que la case cible est valide (brune et dans le plateau)
        if target not in self.cases or (target[0] + target[1]) % 2 == 0:
            self.move_piece_to_cell(orig, self.pion[orig])
            self.click = False
            self.pion_selected = None
            return

        dr = target[0] - orig[0]
        dc = target[1] - orig[1]
        piece_id = self.pion[orig]
        color = self.can.itemcget(piece_id, "fill")
        legal = False
        capture = False
        mid = None

        is_king = orig in self.rois

        # Mouvement normal
        if abs(dr) == 1 and abs(dc) == 1:
            if is_king:
                legal = True
            elif color == "coral" and dr == 1:
                legal = True
            elif color == "cadetblue" and dr == -1:
                legal = True

        # Mouvement de capture
        elif abs(dr) == 2 and abs(dc) == 2:
            mid = ((orig[0] + target[0]) // 2, (orig[1] + target[1]) // 2)
            if mid in self.pion:
                mid_color = self.can.itemcget(self.pion[mid], "fill")
                if mid_color != color:
                    if is_king or (color == "coral" and dr > 0) or (color == "cadetblue" and dr < 0):
                        legal = True
                        capture = True

        # La case d'arrivée doit être vide
        if target in self.pion:
            legal = False

        if legal:
            if capture and mid:
                self.remove_piece(mid, captor=color)
            
            # Déplacer le pion
            self.pion[target] = self.pion.pop(orig)
            
            # Mettre à jour la position du roi si nécessaire
            if orig in self.rois:
                self.rois[target] = self.rois.pop(orig)
                if hasattr(self, 'crowns') and orig in self.crowns:
                    self.crowns[target] = self.crowns.pop(orig)
            
            self.move_piece_to_cell(target, piece_id)
            
            # Vérifier la promotion
            self.check_promotion(target, color)
            
            # Changer de tour
            self.tour_joueur = "cadetblue" if self.tour_joueur == "coral" else "coral"
            
        else:
            # Mouvement illégal : retour à la case d'origine
            self.move_piece_to_cell(orig, piece_id)

        self.click = False
        self.pion_selected = None

    def check_promotion(self, position, color):
        """Vérifie si un pion doit être promu en roi."""
        row, col = position
        
        if color == "coral" and row == 9 and position not in self.rois:
            self.promote_to_king(position)
        elif color == "cadetblue" and row == 0 and position not in self.rois:
            self.promote_to_king(position)

    def promote_to_king(self, position):
        """Transforme un pion en roi."""
        self.rois[position] = True
        
        if not hasattr(self, 'crowns'):
            self.crowns = {}
            
        row, col = position
        cell_width = self.lo / 10
        cell_height = self.la / 10
        center_x = col * cell_width + cell_width / 2
        center_y = row * cell_height + cell_height / 2
        
        font_size = max(12, int(min(cell_width, cell_height) / 3))
        self.crowns[position] = self.can.create_text(
            center_x, center_y, text="K", 
            font=("Arial", font_size, "bold"), fill="gold"
        )

    def get_board_coords(self, x, y):
        """Convertit des coordonnées en pixels en coordonnées de case."""
        col = min(max(0, int(x / (self.lo / 10))), 9)
        row = min(max(0, int(y / (self.la / 10))), 9)
        return (row, col)

    def move_piece_to_cell(self, cell, piece_id):
        """Positionne le pion dans la case donnée."""
        row, col = cell
        cell_width = self.lo / 10
        cell_height = self.la / 10
        margin = min(cell_width, cell_height) * 0.2
        
        x0 = col * cell_width + margin
        y0 = row * cell_height + margin
        x1 = (col + 1) * cell_width - margin
        y1 = (row + 1) * cell_height - margin
        
        self.can.coords(piece_id, x0, y0, x1, y1)
        
        # Déplacer aussi la couronne si c'est un roi
        if cell in self.rois and hasattr(self, 'crowns') and cell in self.crowns:
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            self.can.coords(self.crowns[cell], center_x, center_y)

    def remove_piece(self, cell, captor):
        """Supprime un pion capturé et met à jour le score."""
        if cell in self.pion:
            piece_id = self.pion.pop(cell)
            
            # Supprimer la couronne si c'était un roi
            if cell in self.rois:
                if hasattr(self, 'crowns') and cell in self.crowns:
                    self.can.delete(self.crowns[cell])
                    del self.crowns[cell]
                del self.rois[cell]
            
            self.can.delete(piece_id)
            
            # Mettre à jour le score
            if captor == "coral":
                self.pions_captures["coral"] += 1
                self.score_p1.set(str(self.pions_captures["coral"]))
                self.afficher_pion_capture("cadetblue", self.pions_captures["coral"])
            else:
                self.pions_captures["cadetblue"] += 1
                self.score_p2.set(str(self.pions_captures["cadetblue"]))
                self.afficher_pion_capture("coral", self.pions_captures["cadetblue"])

    def afficher_pion_capture(self, color, count):
        """Affiche un pion capturé dans la zone appropriée."""
        canvas = self.can_bank1 if color == "cadetblue" else self.can_bank2
        
        # Nettoyer la zone avant de redessiner
        canvas.delete("all")
        
        bank_width = canvas.winfo_width()
        bank_height = canvas.winfo_height()
        
        if bank_width > 1 and bank_height > 1:  # Vérifier que le canvas est créé
            # Taille adaptative des pions capturés
            piece_size = min(bank_width, bank_height) * 0.1
            pieces_per_row = max(3, int(bank_width / (piece_size * 1.5)))
            
            for i in range(count):
                row = i // pieces_per_row
                col = i % pieces_per_row
                
                x = piece_size * 0.5 + col * (piece_size * 1.2)
                y = piece_size * 0.5 + row * (piece_size * 1.2)
                
                if y + piece_size < bank_height - piece_size * 0.5:
                    canvas.create_oval(x, y, x + piece_size, y + piece_size, 
                                     fill=color, outline="black", width=2)

if __name__ == "__main__":
    damier = Damier()
    damier.mainloop()