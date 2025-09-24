import tkinter as tk
import platform
from collections import deque

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
            self.attributes('-zoomed', True)
        
        # Dimensions adaptatives du plateau
        self.lo = min(self.w * 0.7, self.h * 0.9)
        self.la = self.lo * 0.75
        
        self.click = False
        self.pion_selected = None
        self.pion_selec_coord = None
        self.pion = {}  # (row, col) -> piece_id
        self.pion_colors = {}  # (row, col) -> color (pour garder la couleur)
        self.cases = {}
        self.pions_captures = {"coral": 0, "cadetblue": 0}
        self.rois = {}
        self.tour_joueur = "coral"
        
        # Historique pour l'annulation
        self.historique = deque(maxlen=20)
        
        # Variables pour les captures multiples
        self.capture_en_cours = False
        self.dernier_pion_captureur = None
        self.captures_possibles = []
        
        # Création du conteneur principal
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
        
        self.create_control_panel()
        self.create_board()
        self.chequer_bank()
        self.create_pieces()

        # Bindings souris sur le canvas
        self.can.bind("<Button-1>", lambda event: self.move_chequer(event))
        self.can.bind("<B1-Motion>", lambda event: self.movep(event))
        self.can.bind("<ButtonRelease-1>", lambda event: self.bring(event))
        
        # Bind pour le redimensionnement
        self.bind("<Configure>", self.on_resize)

    def create_control_panel(self):
        """Crée le panel de contrôle avec les boutons"""
        control_frame = tk.Frame(self.player1_frame, bg="chocolate")
        control_frame.pack(side=tk.BOTTOM, pady=20)
        
        # Bouton Annuler
        btn_annuler = tk.Button(control_frame, text="Annuler", font=("Arial", 12),
                               command=self.annuler_dernier_coup, bg="orange", fg="black")
        btn_annuler.pack(pady=5, fill=tk.X)
        
        # Bouton Recommencer
        btn_recommencer = tk.Button(control_frame, text="Recommencer", font=("Arial", 12),
                                   command=self.recommencer_partie, bg="red", fg="white")
        btn_recommencer.pack(pady=5, fill=tk.X)
        
        # Indicateur de tour
        self.label_tour = tk.Label(control_frame, text="Tour: JOUEUR 1", 
                                  font=("Arial", 14, "bold"), bg="yellow", fg="black")
        self.label_tour.pack(pady=10, fill=tk.X)

    def sauvegarder_etat(self):
        """Sauvegarde l'état actuel du jeu pour l'annulation"""
        etat = {
            'pion': self.pion.copy(),
            'pion_colors': self.pion_colors.copy(),  # Sauvegarder les couleurs
            'rois': self.rois.copy(),
            'pions_captures': self.pions_captures.copy(),
            'tour_joueur': self.tour_joueur,
        }
        return etat

    def restaurer_etat(self, etat):
        """Restaure un état précédent du jeu"""
        # Supprimer tous les éléments graphiques
        self.can.delete("all")
        if hasattr(self, 'crowns'):
            self.crowns.clear()
        
        # Restaurer les données
        self.pion = etat['pion'].copy()
        self.pion_colors = etat['pion_colors'].copy()  # Restaurer les couleurs
        self.rois = etat['rois'].copy()
        self.pions_captures = etat['pions_captures'].copy()
        self.tour_joueur = etat['tour_joueur']
        
        # Recréer le damier
        self.create_board()
        
        # Recréer les pions avec leurs couleurs correctes
        cell_width = self.lo / 10
        cell_height = self.la / 10
        margin = min(cell_width, cell_height) * 0.2
        
        for position in self.pion.keys():
            row, col = position
            x0 = col * cell_width + margin
            y0 = row * cell_height + margin
            x1 = (col + 1) * cell_width - margin
            y1 = (row + 1) * cell_height - margin
            
            # Utiliser la couleur sauvegardée
            color = self.pion_colors.get(position, "coral")
            new_id = self.can.create_oval(x0, y0, x1, y1,
                                         fill=color, outline="black", width=2)
            self.pion[position] = new_id
            
            # Recréer la couronne si c'est un roi
            if position in self.rois:
                self.promote_to_king(position)
        
        # Mettre à jour l'affichage
        self.mettre_a_jour_scores()
        self.mettre_a_jour_affichage_tour()
        self.afficher_pions_captures()

    def annuler_dernier_coup(self):
        """Annule le dernier coup joué"""
        if len(self.historique) > 0:
            etat_precedent = self.historique.pop()
            self.restaurer_etat(etat_precedent)
            self.capture_en_cours = False
            self.dernier_pion_captureur = None
            self.captures_possibles = []

    def recommencer_partie(self):
        """Recommence une nouvelle partie"""
        # Réinitialiser toutes les variables
        self.can.delete("all")
        self.pion.clear()
        self.pion_colors.clear()
        self.cases.clear()
        self.rois.clear()
        self.pions_captures = {"coral": 0, "cadetblue": 0}
        self.tour_joueur = "coral"
        self.capture_en_cours = False
        self.dernier_pion_captureur = None
        self.captures_possibles = []
        self.historique.clear()
        
        if hasattr(self, 'crowns'):
            self.crowns.clear()
        
        # Recréer le jeu
        self.create_board()
        self.create_pieces()
        self.mettre_a_jour_scores()
        self.mettre_a_jour_affichage_tour()

    def mettre_a_jour_scores(self):
        """Met à jour l'affichage des scores"""
        self.score_p1.set(str(self.pions_captures["coral"]))
        self.score_p2.set(str(self.pions_captures["cadetblue"]))
        self.afficher_pions_captures()

    def mettre_a_jour_affichage_tour(self):
        """Met à jour l'affichage du tour"""
        joueur = "JOUEUR 1" if self.tour_joueur == "coral" else "JOUEUR 2"
        self.label_tour.config(text=f"Tour: {joueur}")

    def on_resize(self, event):
        """Redimensionnement adaptatif"""
        if event.widget == self:
            new_w = event.width
            new_h = event.height
            
            self.lo = min(new_w * 0.6, new_h * 0.8)
            self.la = self.lo * 0.75
            
            self.can.config(width=self.lo, height=self.la)
            self.redraw_board()

    def redraw_board(self):
        """Redessine le damier"""
        self.can.delete("all")
        self.create_board()
        
        # Redessiner les pions avec leurs couleurs correctes
        cell_width = self.lo / 10
        cell_height = self.la / 10
        margin = min(cell_width, cell_height) * 0.2
        
        nouvelles_positions = {}
        for position, old_id in list(self.pion.items()):
            row, col = position
            x0 = col * cell_width + margin
            y0 = row * cell_height + margin
            x1 = (col + 1) * cell_width - margin
            y1 = (row + 1) * cell_height - margin
            
            # Utiliser la couleur sauvegardée
            color = self.pion_colors.get(position, "coral")
            new_id = self.can.create_oval(x0, y0, x1, y1, fill=color, outline="black", width=2)
            nouvelles_positions[position] = new_id
            
            if position in self.rois:
                self.promote_to_king(position)
        
        self.pion = nouvelles_positions

    def create_board(self):
        """Crée le damier 10x10"""
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
                    x0, y0, x1, y1, fill=color, outline="black", width=1
                )

    def create_pieces(self):
        """Place les pions initiaux avec leurs couleurs"""
        cell_width = self.lo / 10
        cell_height = self.la / 10
        margin = min(cell_width, cell_height) * 0.2
        
        # Joueur 1 (coral)
        for row in range(0, 4):
            for col in range(10):
                if (row + col) % 2 == 1:
                    x0 = col * cell_width + margin
                    y0 = row * cell_height + margin
                    x1 = (col + 1) * cell_width - margin
                    y1 = (row + 1) * cell_height - margin
                    
                    piece_id = self.can.create_oval(x0, y0, x1, y1, 
                                                   fill="coral", outline="black", width=2)
                    self.pion[(row, col)] = piece_id
                    self.pion_colors[(row, col)] = "coral"  # Sauvegarder la couleur
        
        # Joueur 2 (cadetblue)
        for row in range(6, 10):
            for col in range(10):
                if (row + col) % 2 == 1:
                    x0 = col * cell_width + margin
                    y0 = row * cell_height + margin
                    x1 = (col + 1) * cell_width - margin
                    y1 = (row + 1) * cell_height - margin
                    
                    piece_id = self.can.create_oval(x0, y0, x1, y1, 
                                                   fill="cadetblue", outline="black", width=2)
                    self.pion[(row, col)] = piece_id
                    self.pion_colors[(row, col)] = "cadetblue"  # Sauvegarder la couleur

    def chequer_bank(self):
        """Crée les zones de score"""
        bank_width = self.w * 0.12
        bank_height = self.h * 0.6
        
        # Joueur 1
        self.can_bank1 = tk.Canvas(self.player1_frame, width=bank_width, height=bank_height, 
                                  bg="maroon", bd=3, relief="groove")
        self.can_bank1.pack(pady=20)
        
        tk.Label(self.player1_frame, text="PLAYER 1", font=("Arial", self.get_font_size(20)), 
                bg="chocolate", fg="white").pack(pady=5)
        tk.Label(self.player1_frame, text="SCORE P1", font=("Arial", self.get_font_size(16)), 
                bg="red", fg="white").pack(pady=5)
        
        self.score_p1 = tk.StringVar(value="0")
        self.label_score_p1 = tk.Label(self.player1_frame, textvariable=self.score_p1, 
                                      font=("Georgia", self.get_font_size(18)), 
                                      bg="white", width=8, relief="sunken")
        self.label_score_p1.pack(pady=5)
        
        # Joueur 2
        self.can_bank2 = tk.Canvas(self.player2_frame, width=bank_width, height=bank_height, 
                                  bg="maroon", bd=3, relief="groove")
        self.can_bank2.pack(pady=20)
        
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
        return max(base_size, int(min(self.w, self.h) / 80))

    def move_chequer(self, event):
        """Gère le clic sur un pion"""
        if self.capture_en_cours:
            # En mode capture multiple, on ne peut déplacer que le pion qui a capturé
            x, y = event.x, event.y
            if self.dernier_pion_captureur:
                coords = self.can.coords(self.pion[self.dernier_pion_captureur])
                if coords and len(coords) == 4:
                    if coords[0] < x < coords[2] and coords[1] < y < coords[3]:
                        self.pion_selected = self.dernier_pion_captureur
                        self.pion_selec_coord = coords
                        self.click = True
            return
        
        x, y = event.x, event.y
        for position, piece_id in self.pion.items():
            coords = self.can.coords(piece_id)
            if coords and len(coords) == 4:
                if coords[0] < x < coords[2] and coords[1] < y < coords[3]:
                    color = self.pion_colors.get(position)  # Utiliser le dictionnaire des couleurs
                    if color == self.tour_joueur:
                        self.pion_selected = position
                        self.pion_selec_coord = coords
                        self.click = True
                        break

    def movep(self, event):
        """Déplacement temporaire du pion"""
        if self.click and self.pion_selected:
            x1, y1 = event.x, event.y
            piece_id = self.pion[self.pion_selected]
            size = min(self.lo, self.la) / 30
            self.can.coords(piece_id, x1 - size, y1 - size, x1 + size, y1 + size)

    def bring(self, event):
        """Valide le déplacement"""
        if not self.pion_selected:
            return

        # Sauvegarder l'état avant le coup
        etat_avant = self.sauvegarder_etat()
        self.historique.append(etat_avant)

        orig = self.pion_selected
        target = self.get_board_coords(event.x, event.y)
        
        if self.valider_deplacement(orig, target):
            self.effectuer_deplacement(orig, target)
        else:
            self.move_piece_to_cell(orig, self.pion[orig])

        self.click = False
        self.pion_selected = None

    def valider_deplacement(self, orig, target):
        """Valide si le déplacement est légal"""
        if target not in self.cases or (target[0] + target[1]) % 2 == 0:
            return False

        if target in self.pion:
            return False

        dr = target[0] - orig[0]
        dc = target[1] - orig[1]
        color = self.pion_colors.get(orig)  # Utiliser le dictionnaire des couleurs
        is_king = orig in self.rois

        # Vérifier les captures possibles en premier (obligatoires)
        captures = self.get_captures_possibles(color)
        if captures:
            for capture in captures:
                if capture[0] == orig and capture[1] == target:
                    return True
            return False

        # Mouvement simple (seulement si pas de captures obligatoires)
        if abs(dr) == 1 and abs(dc) == 1:
            if is_king:
                return True
            elif color == "coral" and dr == 1:
                return True
            elif color == "cadetblue" and dr == -1:
                return True

        return False

    def get_captures_possibles(self, color):
        """Retourne toutes les captures possibles pour un joueur"""
        captures = []
        for position in self.pion.keys():
            if self.pion_colors.get(position) == color:  # Utiliser le dictionnaire des couleurs
                captures.extend(self.get_captures_pour_pion(position))
        return captures

    def get_captures_pour_pion(self, position):
        """Retourne les captures possibles pour un pion spécifique"""
        captures = []
        directions = self.get_directions_pion(position)
        
        for dr, dc in directions:
            mid = (position[0] + dr, position[1] + dc)
            target = (position[0] + 2*dr, position[1] + 2*dc)
            
            if (self.est_case_valide(mid) and self.est_case_valide(target) and
                mid in self.pion and target not in self.pion):
                mid_color = self.pion_colors.get(mid)  # Utiliser le dictionnaire des couleurs
                position_color = self.pion_colors.get(position)  # Utiliser le dictionnaire des couleurs
                if mid_color != position_color:
                    captures.append((position, target, mid))
        
        return captures

    def get_directions_pion(self, position):
        """Retourne les directions possibles pour un pion"""
        color = self.pion_colors.get(position)  # Utiliser le dictionnaire des couleurs
        is_king = position in self.rois
        
        if is_king:
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif color == "coral":
            return [(1, -1), (1, 1)]
        else:
            return [(-1, -1), (-1, 1)]

    def est_case_valide(self, case):
        """Vérifie si une case est valide et brune"""
        return (case in self.cases and (case[0] + case[1]) % 2 == 1 and
                0 <= case[0] < 10 and 0 <= case[1] < 10)

    def effectuer_deplacement(self, orig, target):
        """Effectue le déplacement et gère les captures"""
        dr = target[0] - orig[0]
        dc = target[1] - orig[1]
        color = self.pion_colors.get(orig)  # Utiliser le dictionnaire des couleurs

        # Vérifier si c'est une capture
        if abs(dr) == 2 and abs(dc) == 2:
            mid = ((orig[0] + target[0]) // 2, (orig[1] + target[1]) // 2)
            if mid in self.pion:
                self.remove_piece(mid, captor=color)
                self.capture_en_cours = True
                self.dernier_pion_captureur = target
                
                # Vérifier s'il y a d'autres captures possibles depuis la nouvelle position
                nouvelles_captures = self.get_captures_pour_pion(target)
                if nouvelles_captures:
                    self.captures_possibles = nouvelles_captures
                    return
                else:
                    self.capture_en_cours = False
                    self.dernier_pion_captureur = None
                    self.captures_possibles = []
                    self.tour_joueur = "cadetblue" if self.tour_joueur == "coral" else "coral"
        else:
            # Mouvement simple
            self.capture_en_cours = False
            self.dernier_pion_captureur = None
            self.captures_possibles = []
            self.tour_joueur = "cadetblue" if self.tour_joueur == "coral" else "coral"

        # Déplacer le pion et sa couleur
        piece_id = self.pion.pop(orig)
        self.pion[target] = piece_id
        
        # Déplacer aussi la couleur
        if orig in self.pion_colors:
            self.pion_colors[target] = self.pion_colors.pop(orig)
        
        # Déplacer le statut roi si nécessaire
        if orig in self.rois:
            self.rois[target] = self.rois.pop(orig)
            if hasattr(self, 'crowns') and orig in self.crowns:
                self.crowns[target] = self.crowns.pop(orig)
        
        self.move_piece_to_cell(target, piece_id)
        self.check_promotion(target, color)
        self.mettre_a_jour_affichage_tour()

    def move_piece_to_cell(self, cell, piece_id):
        """Positionne le pion dans une case"""
        row, col = cell
        cell_width = self.lo / 10
        cell_height = self.la / 10
        margin = min(cell_width, cell_height) * 0.2
        
        x0 = col * cell_width + margin
        y0 = row * cell_height + margin
        x1 = (col + 1) * cell_width - margin
        y1 = (row + 1) * cell_height - margin
        
        self.can.coords(piece_id, x0, y0, x1, y1)
        
        if cell in self.rois and hasattr(self, 'crowns') and cell in self.crowns:
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            self.can.coords(self.crowns[cell], center_x, center_y)

    def check_promotion(self, position, color):
        """Vérifie la promotion en roi"""
        row = position[0]
        if (color == "coral" and row == 9) or (color == "cadetblue" and row == 0):
            if position not in self.rois:
                self.promote_to_king(position)

    def promote_to_king(self, position):
        """Promouvoir un pion en roi"""
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

    def remove_piece(self, cell, captor):
        """Supprime un pion capturé"""
        if cell in self.pion:
            piece_id = self.pion.pop(cell)
            
            # Supprimer aussi la couleur
            if cell in self.pion_colors:
                self.pion_colors.pop(cell)
            
            if cell in self.rois:
                if hasattr(self, 'crowns') and cell in self.crowns:
                    self.can.delete(self.crowns[cell])
                    del self.crowns[cell]
                del self.rois[cell]
            
            self.can.delete(piece_id)
            
            if captor == "coral":
                self.pions_captures["coral"] += 1
            else:
                self.pions_captures["cadetblue"] += 1
            
            self.mettre_a_jour_scores()

    def afficher_pions_captures(self):
        """Affiche les pions capturés"""
        for canvas, color, count in [
            (self.can_bank1, "cadetblue", self.pions_captures["coral"]),
            (self.can_bank2, "coral", self.pions_captures["cadetblue"])
        ]:
            canvas.delete("all")
            bank_width = canvas.winfo_width()
            bank_height = canvas.winfo_height()
            
            if bank_width > 1 and bank_height > 1:
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

    def get_board_coords(self, x, y):
        """Convertit les coordonnées pixels en coordonnées case"""
        col = min(max(0, int(x / (self.lo / 10))), 9)
        row = min(max(0, int(y / (self.la / 10))), 9)
        return (row, col)

if __name__ == "__main__":
    damier = Damier()
    damier.mainloop()