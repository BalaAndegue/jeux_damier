import tkinter as tk

class Damier(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config(bg="chocolate")
        self.title("MON SIMPLE DAMIER")
        self.w, self.h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{self.w}x{self.h}")
        # Dimensions du plateau (en pixels)
        self.lo, self.la = 1000, 750  
        self.click = False
        self.pion_selected = None  # Coordonnées (row, col) du pion sélectionné
        self.pion_selec_coord = None  # Coordonnées initiales (en pixels) du pion
        self.pion = {}   # Dictionnaire : (row, col) -> id du pion sur le canvas
        self.cases = {}  # Dictionnaire : (row, col) -> id de la case sur le canvas

        self.can = tk.Canvas(self, width=self.lo, height=self.la, bg="burlywood",
                              bd=5, borderwidth=5, relief="groove")
        self.can.pack()

        self.create_board()     # Création du damier (10x10)
        self.chequer_bank()     # Création des zones pour les pièces capturées (prison)
        self.create_pieces()    # Placement initial des pions

        # Bindings souris
        self.bind("<Button-1>", lambda event: self.move_chequer(event))
        self.bind("<B1-Motion>", lambda event: self.movep(event))
        self.bind("<ButtonRelease-1>", lambda event: self.bring(event))

    def create_board(self):
        """Création d'un damier 10x10.
           Seules les cases foncées (où (row+col)%2 == 1) seront utilisées pour le jeu."""
        cell_width = self.lo / 10
        cell_height = self.la / 10
        for row in range(10):
            for col in range(10):
                # Définir la couleur de la case (alternance)
                color = "brown" if (row + col) % 2 == 1 else "burlywood"
                self.cases[(row, col)] = self.can.create_rectangle(
                    col * cell_width, row * cell_height,
                    (col + 1) * cell_width, (row + 1) * cell_height,
                    fill=color, outline="black"
                )

    def create_pieces(self):
        """Placement initial des pions.
        - Joueur 1 (coral) sur les 4 premières lignes (cases foncées)
        - Joueur 2 (cadetblue) sur les 4 dernières lignes (cases foncées)"""
        cell_width = self.lo / 10
        cell_height = self.la / 10
        # Joueur 1 : lignes 0 à 3
        for row in range(0, 4):
            for col in range(10):
                if (row + col) % 2 == 1:
                    piece_id = self.can.create_oval(
                        col * cell_width + 10, row * cell_height + 10,
                        (col + 1) * cell_width - 10, (row + 1) * cell_height - 10,
                        fill="coral", outline="black", width=2
                    )
                    self.pion[(row, col)] = piece_id
        # Joueur 2 : lignes 6 à 9
        for row in range(6, 10):
            for col in range(10):
                if (row + col) % 2 == 1:
                    piece_id = self.can.create_oval(
                        col * cell_width + 10, row * cell_height + 10,
                        (col + 1) * cell_width - 10, (row + 1) * cell_height - 10,
                        fill="cadetblue", outline="black", width=2
                    )
                    self.pion[(row, col)] = piece_id

    def chequer_bank(self):
        """Création des zones (prison) pour les pièces capturées.
        Ici, on affiche deux zones latérales pour PLAYER 1 et PLAYER 2."""
        entry1 = tk.Entry(self, width=10, font=("Georgia", 17))
        entry2 = tk.Entry(self, width=10, font=("Georgia", 17))
        self.can_bank1 = tk.Canvas(self, width=200, height=450, bg="maroon",
                                    bd=5, borderwidth=5, relief="groove")
        self.can_bank1.place(x=0, y=50)
        tk.Label(self, text="PLAYER 1", font=("Arial", 20), bg="chocolate").place(x=10, y=5)
        tk.Label(self, text="SCORE P1", font=("Arial", 17), bg="red").place(x=0, y=600)
        entry1.place(x=0, y=632)
        entry2.place(x=1330, y=632)
        self.can_bank2 = tk.Canvas(self, width=200, height=450, bg="maroon",
                                    bd=5, borderwidth=5, relief="groove")
        self.can_bank2.place(x=1330, y=50)
        tk.Label(self, text="PLAYER 2", font=("Arial", 20), bg="chocolate").place(x=1340, y=5)
        tk.Label(self, text="SCORE P2", font=("Arial", 17), bg="red").place(x=1330, y=600)

    def move_chequer(self, event):
        """Lors d'un clic, on détermine si l'on clique sur un pion."""
        x, y = event.x, event.y
        for position, piece_id in self.pion.items():
            coords = self.can.coords(piece_id)  # [x0, y0, x1, y1]
            if coords and (coords[0] < x < coords[2]) and (coords[1] < y < coords[3]):
                self.pion_selected = position  # Coordonnées (row, col)
                self.pion_selec_coord = coords
                self.click = True
                break

    def movep(self, event):
        """Déplacement temporaire du pion avec la souris (pendant le drag)."""
        if self.click and self.pion_selected:
            x1, y1 = event.x, event.y
            piece_id = self.pion[self.pion_selected]
            # On déplace le pion autour de la position de la souris (sans le coller à la grille)
            self.can.coords(piece_id, x1 - 27, y1 - 22.5, x1 + 27, y1 + 22.5)

    def bring(self, event):
        """
        Lors du relâchement de la souris, on essaie de valider le déplacement.
        Le pion doit se déplacer en diagonale :
        - Mouvement normal : d'une case diagonale dans la bonne direction (coral vers le bas, cadetblue vers le haut)
        - Capture : saut de deux cases en diagonale, si la case intermédiaire contient un pion adverse
        Si le mouvement est légal, on met à jour la position.
        Sinon, on réaffiche le pion à sa position d'origine.
        """
        if not self.pion_selected:
            return

        orig = self.pion_selected  # position d'origine (row, col)
        target = self.get_board_coords(event.x, event.y)
        if target not in self.cases:
            self.move_piece_to_cell(orig, self.pion[self.pion_selected])
            self.click = False
            self.pion_selected = None
            return

        dr = target[0] - orig[0]
        dc = target[1] - orig[1]
        piece_id = self.pion[orig]
        color = self.can.itemcget(piece_id, "fill")  # "coral" ou "cadetblue"
        legal = False
        capture = False

        # Mouvement normal (une case en diagonale)
        if abs(dr) == 1 and abs(dc) == 1:
            if color == "coral" and dr == 1:
                legal = True
            elif color == "cadetblue" and dr == -1:
                legal = True

        # Mouvement de capture (deux cases en diagonale)
        elif abs(dr) == 2 and abs(dc) == 2:
            mid = ((orig[0] + target[0]) // 2, (orig[1] + target[1]) // 2)
            if mid in self.pion:
                mid_piece_id = self.pion[mid]
                mid_color = self.can.itemcget(mid_piece_id, "fill")
                if mid_color != color:
                    legal = True
                    capture = True

        # La case d'arrivée doit être vide
        if target in self.pion:
            legal = False

        if legal:
            # Si capture, on retire le pion adverse
            if capture:
                mid = ((orig[0] + target[0]) // 2, (orig[1] + target[1]) // 2)
                self.remove_piece(mid, captor=color)
            # Mise à jour du dictionnaire de pièces : on déplace la clé
            self.pion[target] = self.pion.pop(orig)
            self.move_piece_to_cell(target, piece_id)
        else:
            # Mouvement illégal : retour à la case d'origine
            self.move_piece_to_cell(orig, piece_id)

        self.click = False
        self.pion_selec_coord = None
        self.pion_selected = None

    def get_board_coords(self, x, y):
        """Convertit des coordonnées en pixels en coordonnées de case (row, col)."""
        col = int(x / (self.lo / 10))
        row = int(y / (self.la / 10))
        return (row, col)

    def move_piece_to_cell(self, cell, piece_id):
        """Positionne le pion dans la case donnée (en ajustant les marges pour l'esthétique)."""
        row, col = cell
        x0 = self.lo * col / 10
        y0 = self.la * row / 10
        x1 = self.lo * (col + 1) / 10
        y1 = self.la * (row + 1) / 10
        self.can.coords(piece_id, x0 + 10, y0 + 10, x1 - 10, y1 - 10)

    def remove_piece(self, cell, captor):
        """
        Supprime le pion adverse se trouvant à 'cell' et l'envoie (ici, on le supprime du plateau).
        'captor' est la couleur du joueur qui capture.
        Vous pourrez étendre cette fonction pour ajouter le pion capturé à une zone de prison.
        """
        if cell in self.pion:
            piece_id = self.pion.pop(cell)
            self.can.delete(piece_id)
            print(f"Piece en {cell} capturée par {captor}.")

if __name__ == "__main__":
    damier = Damier()
    damier.mainloop()
