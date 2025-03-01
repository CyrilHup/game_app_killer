from supabase import create_client, Client
import tkinter as tk
from tkinter import messagebox
import math
import sys
import difflib
import uuid
import os
import appdirs
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_data():
    response = supabase.table('individus').select('*, info').execute()
    data = response.data
    for ind in data:
        ind['id'] = str(ind['id'])
        ind['nom'] = ind['nom'].lower()
        if ind['kill'] is not None:
            ind['kill'] = str(ind['kill'])
    return data

def fetch_password():
    response = supabase.table('settings').select('password').execute()
    if response.data and 'password' in response.data[0]:
        return response.data[0]['password']
    else:
        return None

def get_installation_id():
    app_name = 'KillerApp'
    install_id_dir = appdirs.user_data_dir(app_name)
    install_id_file = os.path.join(install_id_dir, 'install_id.txt')
    if os.path.exists(install_id_file):
        with open(install_id_file, 'r') as f:
            install_id = f.read().strip()
    else:
        os.makedirs(install_id_dir, exist_ok=True)
        install_id = str(uuid.uuid4())
        with open(install_id_file, 'w') as f:
            f.write(install_id)
    return install_id

def register_installation(install_id, username):
    response = supabase.table('installations').select('*').eq('install_id', install_id).execute()
    if not response.data:
        supabase.table('installations').insert({'install_id': install_id, 'username': username}).execute()
    else:
        supabase.table('installations').update({'username': username}).eq('install_id', install_id).execute()

def prompt_for_username():
    prompt_root = tk.Toplevel()
    prompt_root.title("Entrez votre nom")
    prompt_root.geometry("300x150")
    tk.Label(prompt_root, text="Veuillez entrer votre nom:").pack(pady=10)
    name_entry = tk.Entry(prompt_root, width=30)
    name_entry.pack(pady=5)
    name_var = tk.StringVar()

    def submit_name():
        name = name_entry.get().strip()
        if name:
            name_var.set(name)
            prompt_root.destroy()
        else:
            tk.messagebox.showerror("Erreur", "Le nom ne peut pas être vide.")

    name_entry.bind("<Return>", lambda event: submit_name())
    tk.Button(prompt_root, text="Valider", command=submit_name).pack(pady=10)
    prompt_root.wait_window()
    return name_var.get()

def create_login_screen():
    login_root = tk.Tk()
    login_root.title("Login")
    login_root.geometry("300x150")
    tk.Label(login_root, text="Veuillez entrer le mot de passe:").pack(pady=10)
    password_entry = tk.Entry(login_root, show="*", width=30)
    password_entry.pack(pady=5)

    def check_password():
        entered_password = password_entry.get()
        stored_password = fetch_password()
        if entered_password == stored_password:
            install_id = get_installation_id()
            response = supabase.table('installations').select('*').eq('install_id', install_id).execute()
            if not response.data:
                username = prompt_for_username()
                register_installation(install_id, username)
            else:
                username = response.data[0]['username']
                if not username:
                    username = prompt_for_username()
                    register_installation(install_id, username)
            login_root.destroy()
            create_gui(username)
        else:
            tk.messagebox.showerror("Erreur", "Mot de passe incorrect.")

    password_entry.bind("<Return>", lambda event: check_password())
    tk.Button(login_root, text="Se connecter", command=check_password).pack(pady=10)
    login_root.mainloop()

def create_gui(username):
    current_user = username
    root = tk.Tk()
    root.title("Killer App")
    root.state('zoomed')

    for row in range(3):
        if row < 2:
            root.grid_rowconfigure(row, weight=0)
        else:
            root.grid_rowconfigure(row, weight=1)
    for i in range(6):
        root.grid_columnconfigure(i, weight=1)

    popup = None
    selected_node_id = None
    resize_job = None
    current_highlight_ids_by_name = []
    current_highlight_ids_by_info = []
    show_names = True
    show_5a_filter = False
    name_font_size = 7

    def update_status(message, is_error=False):
        status_label.config(text=message, fg="red" if is_error else "green")
        root.after(3000, lambda: status_label.config(text=""))

    def toggle_names():
        nonlocal show_names
        show_names = not show_names
        button_toggle_names.config(text="Cacher les noms" if show_names else "Afficher les noms")
        draw_individus()

    def toggle_5a_filter():
        nonlocal show_5a_filter
        show_5a_filter = not show_5a_filter
        button_5a_filter.config(text="Désactiver 5A" if show_5a_filter else "Activer 5A")
        draw_individus()

    def search_node():
        nonlocal selected_node_id, current_highlight_ids_by_name
        name = search_entry.get().strip().lower()
        data = fetch_data()
        if not name:
            current_highlight_ids_by_name.clear()
            update_status("Aucun nœud sélectionné.")
        else:
            matching_inds = [ind for ind in data if name in ind['nom'] or difflib.SequenceMatcher(None, name, ind['nom']).ratio() > 0.6]
            if matching_inds:
                selected_node_id = matching_inds[0]['id']
                current_highlight_ids_by_name.clear()
                current_highlight_ids_by_name.extend([ind['id'] for ind in matching_inds])
                update_status(f"{len(matching_inds)} nœud(s) trouvé(s) correspondant(s).")
            else:
                update_status(f"Aucun noeud trouvé avec le nom '{name}'.", is_error=True)
                selected_node_id = None
                current_highlight_ids_by_name.clear()
        draw_individus()

    def search_infos():
        query = search_info_entry.get().strip().lower()
        data = fetch_data()
        if not query:
            current_highlight_ids_by_info.clear()
            update_status("Aucun nœud sélectionné.")
        else:
            matching_ids = [ind['id'] for ind in data if query in (ind.get('info') or '').lower()]
            if matching_ids:
                update_status(f"{len(matching_ids)} nœud(s) trouvé(s) contenant '{query}'.")
                current_highlight_ids_by_info.clear()
                current_highlight_ids_by_info.extend(matching_ids)
            else:
                update_status(f"Aucun nœud trouvé contenant '{query}'.", is_error=True)
                current_highlight_ids_by_info.clear()
        draw_individus()

    def draw_individus():
        canvas.delete("all")
        individus = fetch_data()
        positions = {}

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        min_dimension = min(canvas_width, canvas_height)
        center_x, center_y = canvas_width / 2, canvas_height / 2
        canvas_radius = (min_dimension / 2) - 30

        id_to_ind = {ind['id']: ind for ind in individus}

        kill_dict = {ind['id']: ind['kill'] for ind in individus}

        def topological_sort(kill_dict):
            from collections import defaultdict, deque

            graph = defaultdict(list)
            in_degree = defaultdict(int)
            for killer, victim in kill_dict.items():
                if victim:
                    graph[killer].append(victim)
                    in_degree[victim] += 1

            queue = deque(sorted([node for node in kill_dict if in_degree[node] == 0]))
            sorted_nodes = []

            while queue:
                node = queue.popleft()
                sorted_nodes.append(node)
                for neighbor in sorted(graph[node], key=lambda x: x):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            for node in sorted(kill_dict):
                if node not in sorted_nodes:
                    sorted_nodes.append(node)

            return sorted_nodes

        sorted_ids = topological_sort(kill_dict)
        ordered_individus = [id_to_ind[id_] for id_ in sorted_ids if id_ in id_to_ind]

        def detect_chains(ordered_individus, kill_dict):
            chains = []
            visited = set()

            for ind in ordered_individus:
                if ind['id'] not in visited:
                    chain = []
                    current = ind
                    while current and current['id'] not in visited:
                        chain.append(current)
                        visited.add(current['id'])
                        victim_id = current['kill']
                        current = id_to_ind.get(victim_id) if victim_id else None
                    chains.append(chain)
            return chains

        chains = detect_chains(ordered_individus, kill_dict)
        chains.sort(key=lambda x: -len(x))

        chain = []
        for i, single_chain in enumerate(chains):
            chain.extend(single_chain)
            if i < len(chains) - 1:
                chain.append({'id': f'ghost_{i}', 'nom': 'Fantôme', 'kill': None})

        total_nodes = sum(1 for ind in chain if ind['nom'] != 'Fantôme')
        angle_gap = (2 * math.pi) / total_nodes if total_nodes > 0 else 0

        node_radius = max(5, min(20, (canvas_radius * math.pi) / (2 * total_nodes)))
        index_real_node = 0
        adjusted_canvas_radius = canvas_radius * zoom_level
        adjusted_node_radius = node_radius * zoom_level

        # Préparer les ensembles pour le filtrage des noms
        nodes_with_5a = set()
        nodes_to_show_names = set()

        if show_5a_filter:
            # Trouver les nœuds avec '5a' dans leur 'info'
            for ind in individus:
                if '5a' in (ind.get('info') or '').lower():
                    nodes_with_5a.add(ind['id'])

            # Ajouter les nœuds adjacents
            for ind_id in nodes_with_5a:
                ind = id_to_ind[ind_id]
                nodes_to_show_names.add(ind_id)
                # Ajouter le 'kill' target
                if ind['kill']:
                    nodes_to_show_names.add(ind['kill'])
                # Ajouter les nœuds qui ont ce nœud comme 'kill' target
                for other_ind in individus:
                    if other_ind['kill'] == ind_id:
                        nodes_to_show_names.add(other_ind['id'])

        for index, ind in enumerate(chain):
            if ind['nom'] == 'Fantôme':
                continue
            angle = -index_real_node * angle_gap
            x = center_x + adjusted_canvas_radius * math.cos(angle)
            y = center_y + adjusted_canvas_radius * math.sin(angle)
            positions[ind['id']] = (x, y)

            # Determine if the node is on the sides or top/bottom
            if abs(math.cos(angle)) > abs(math.sin(angle)):
                # Node is on the left/right sides
                name = ind['nom']
                is_side_node = True
            else:
                # Node is on the top/bottom
                name = '\n'.join(ind['nom'].split())
                is_side_node = False

            font = ('Helvetica', max(6, name_font_size), 'bold')
            node_fill = current_theme["node_fill"]
            if ind['id'] == selected_node_id:
                node_fill = "yellow"
            elif ind['id'] in current_highlight_ids_by_name:
                node_fill = "yellow"
            elif ind['id'] in current_highlight_ids_by_info:
                node_fill = "red"

            # Adjustments for the 5A filter
            display_name = name.upper() if show_names else ""
            if show_5a_filter:
                if ind['id'] in nodes_to_show_names:
                    pass  # Name is displayed normally
                else:
                    display_name = ""  # Hide the name

            canvas.create_oval(
                x - adjusted_node_radius, y - adjusted_node_radius,
                x + adjusted_node_radius, y + adjusted_node_radius,
                fill=node_fill,
                tags=("individu", ind['id'])
            )

            projection_distance = 45
            adjusted_projection_distance = projection_distance * zoom_level
            projected_x = x + adjusted_projection_distance * math.cos(angle)
            projected_y = y + adjusted_projection_distance * math.sin(angle)
            text_x, text_y = projected_x, projected_y

            # Determine the anchor for the text based on node position
            if is_side_node:
                if math.cos(angle) > 0:
                    # Node is on the right side
                    text_anchor = 'w'  # Text starts at (text_x, text_y)
                else:
                    # Node is on the left side
                    text_anchor = 'e'  # Text ends at (text_x, text_y)
            else:
                # Node is at top/bottom
                text_anchor = 'center'

            canvas.create_text(
                text_x, text_y,
                text=display_name.title(),
                fill=current_theme["fg"],
                font=font,
                anchor=text_anchor,
                tags=("individu", ind['id'])
            )
            index_real_node += 1



        def on_individu_click(event, positions):
            try:
                x_click = canvas.canvasx(event.x)
                y_click = canvas.canvasy(event.y)
            except Exception as e:
                print(f"Erreur lors de l'assignation des coordonnées: {e}")
                return
            clicked_items = canvas.find_overlapping(x_click, y_click, x_click, y_click)
            for item in clicked_items:
                tags = canvas.gettags(item)
                if "individu" in tags:
                    ind_id = tags[1]
                    individu = next((ind for ind in fetch_data() if str(ind['id']) == ind_id), None)
                    if individu:
                        show_popup(event.x_root, event.y_root - 50, individu)
                    break

        canvas.tag_bind("individu", "<Button-1>", lambda event, ids=positions: on_individu_click(event, ids))

        for ind in ordered_individus:
            if ind['kill']:
                killer_pos = positions.get(ind['id'])
                victim_id = ind['kill']
                victim_pos = positions.get(victim_id)
                if killer_pos and victim_pos:
                    dx = victim_pos[0] - killer_pos[0]
                    dy = victim_pos[1] - killer_pos[1]
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance == 0:
                        continue
                    offset_x = (dx / distance) * node_radius
                    offset_y = (dy / distance) * node_radius
                    start_x = killer_pos[0] + offset_x
                    start_y = killer_pos[1] + offset_y
                    end_x = victim_pos[0] - offset_x
                    end_y = victim_pos[1] - offset_y

                    canvas.create_line(
                        start_x, start_y,
                        end_x, end_y,
                        arrow=tk.LAST,
                        fill=current_theme["fg"],
                        tags=("arrow",)
                    )

        canvas.configure(scrollregion=(-10000, -10000, 10000, 10000))

    def show_popup(x, y, individu):
        popup_width = 300
        popup_height = 175

        app_x = root.winfo_rootx()
        app_y = root.winfo_rooty()
        app_width = root.winfo_width()
        app_height = root.winfo_height()

        app_left = app_x
        app_top = app_y
        app_right = app_x + app_width
        app_bottom = app_y + app_height

        if x + popup_width > app_right:
            x = x - popup_width
            if x < app_left:
                x = app_right - popup_width
        elif x < app_left:
            x = x + popup_width
            if x + popup_width > app_right:
                x = app_left

        if y + popup_height > app_bottom:
            y = y - popup_height
            if y < app_top:
                y = app_bottom - popup_height
        elif y < app_top:
            y = y + popup_height
            if y + popup_height > app_bottom:
                y = app_top

        nonlocal popup
        if popup:
            popup.destroy()
        popup = tk.Toplevel(root)
        popup.wm_overrideredirect(True)
        popup.configure(bg='white', borderwidth=3, relief='solid')
        popup.wm_geometry(f"+{int(x)}+{int(y)}")
        popup.wm_minsize(width=popup_width, height=popup_height)
        popup.grid_rowconfigure(0, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        text_widget = tk.Text(
            popup,
            bg='white',
            wrap='word',
            width=35,
            height=6
        )
        text_widget.insert(tk.END, str(individu.get('info', 'Aucune information disponible')))
        text_widget.pack(padx=10, pady=10)

        popup.info_text = text_widget
        popup.current_individu = individu
        popup.focus_set()
        popup.bind("<FocusOut>", lambda e: hide_popup())

        tk.Label(popup, text="Nouvelle cible de kill:").pack(padx=10, pady=5)
        kill_entry_field = tk.Entry(popup, width=25)
        if individu.get('kill'):
            kill_nom = next((ind['nom'] for ind in fetch_data() if ind['id'] == individu['kill']), "")
            kill_entry_field.insert(0, kill_nom)
        kill_entry_field.pack(padx=10, pady=5)
        popup.kill_entry_field = kill_entry_field

        delete_button = tk.Button(popup, text="A été kill/supprimer", command=lambda: delete_individu_popup(individu))
        delete_button.pack(padx=10, pady=5)

        tk.Label(popup, text="Nom:").pack(padx=10, pady=5)
        name_entry = tk.Entry(popup, width=25)
        name_entry.insert(0, individu['nom'])
        name_entry.pack(padx=10, pady=5)
        popup.name_entry = name_entry

    def hide_popup(event=None):
        nonlocal popup
        if popup:
            popup.unbind("<FocusOut>")

            new_info = popup.info_text.get("1.0", 'end-1c')
            new_name = popup.name_entry.get().strip()
            new_kill_nom = popup.kill_entry_field.get().strip()
            individu = popup.current_individu

            original_info = individu.get('info', '')
            original_name = individu['nom']
            original_kill_nom = next((ind['nom'] for ind in fetch_data() if ind['id'] == individu['kill']), "") if individu['kill'] else ""

            if (new_info != original_info or
                new_name != original_name or
                new_kill_nom != original_kill_nom):
                update_kill_target(individu, new_kill_nom)
                supabase.table('individus').update({"nom": new_name, "info": new_info}).eq("id", individu['id']).execute()
                action_desc = f"Individu '{original_name}' mis à jour (nom: '{new_name}', info modifiée)"
                supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
                draw_individus()

            popup.destroy()
            popup = None

    def update_kill_target(individu, new_kill_nom):
        if new_kill_nom:
            new_kill_nom = new_kill_nom.strip().lower()
            new_kill = next((ind for ind in fetch_data() if ind['nom'] == new_kill_nom), None)
            if new_kill:
                supabase.table('individus').update({"kill": new_kill['id']}).eq("id", individu['id']).execute()
                action_desc = f"Kill de '{individu['nom']}' mis à jour vers '{new_kill_nom}'"
                supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
            else:
                response = supabase.table('individus').insert({"nom": new_kill_nom, "kill": None}).execute()
                new_kill_id = str(response.data[0]['id'])
                supabase.table('individus').update({"kill": new_kill_id}).eq("id", individu['id']).execute()
                action_desc = f"Nouvel individu '{new_kill_nom}' créé et assigné comme kill de '{individu['nom']}'"
                supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
        else:
            supabase.table('individus').update({"kill": None}).eq("id", individu['id']).execute()
            action_desc = f"Kill de '{individu['nom']}' supprimé"
            supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()

    def delete_individu_popup(individu):
        supabase.table('individus').update({"kill": individu['kill']}).eq("kill", individu['id']).execute()
        supabase.table('individus').delete().eq("id", individu['id']).execute()
        update_status(f"Individu '{individu['nom']}' supprimé avec succès.")
        action_desc = f"Individu '{individu['nom']}' supprimé"
        supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
        hide_popup()
        draw_individus()

    def delete_individu():
        nom = delete_entry.get().strip().lower()
        if not nom:
            update_status("Veuillez entrer un nom à supprimer.", is_error=True)
            return
        individus = fetch_data()
        individu_to_delete = next((ind for ind in individus if ind['nom'] == nom), None)
        if not individu_to_delete:
            update_status(f"Individu '{nom}' non trouvé.", is_error=True)
            return
        kill_id = individu_to_delete['kill']
        supabase.table('individus').update({"kill": kill_id}).eq("kill", individu_to_delete['id']).execute()
        supabase.table('individus').delete().eq("id", individu_to_delete['id']).execute()
        update_status(f"Individu '{nom}' supprimé avec succès.")
        action_desc = f"Individu '{nom}' supprimé"
        supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
        draw_individus()

    tk.Label(root, text="Supprimer Nom:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    delete_entry = tk.Entry(root, width=20)
    delete_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
    delete_entry.bind('<Return>', lambda event: delete_individu())
    tk.Button(root, text="Supprimer", command=delete_individu, width=10).grid(row=0, column=2, padx=10, pady=5, sticky="w")

    tk.Label(root, text="Rechercher Nom:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    search_entry = tk.Entry(root, width=20)
    search_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
    search_entry.bind('<Return>', lambda event: search_node())
    tk.Button(root, text="Rechercher", command=search_node, width=10).grid(row=1, column=2, padx=10, pady=5, sticky="w")

    button_toggle_names = tk.Button(root, text="Cacher les noms", command=toggle_names)
    button_toggle_names.grid(row=1, column=3, padx=10, pady=5, sticky="w")

    button_5a_filter = tk.Button(root, text="Activer 5A", command=toggle_5a_filter)
    button_5a_filter.grid(row=1, column=4, padx=10, pady=5, sticky="w")

    tk.Label(root, text="Rechercher Infos:").grid(row=1, column=5, padx=10, pady=5, sticky="w")
    search_info_entry = tk.Entry(root, width=20)
    search_info_entry.grid(row=1, column=6, padx=10, pady=5, sticky="w")
    search_info_entry.bind('<Return>', lambda event: search_infos())
    tk.Button(root, text="Rechercher", command=search_infos, width=10).grid(row=1, column=7, padx=10, pady=5, sticky="w")

    status_label = tk.Label(root, text="", fg="green")
    status_label.grid(row=3, column=0, columnspan=8, padx=10, pady=5, sticky="w")

    canvas = tk.Canvas(root, bg="white")
    canvas.grid(row=2, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")

    zoom_level = 1.0
    pan_start_x = 0
    pan_start_y = 0
    base_font_size = 7

    def zoom(event):
        nonlocal zoom_level
        scale = 1.0
        if event.num == 4 or event.delta > 0:
            scale = 1.1
        elif event.num == 5 or event.delta < 0:
            scale = 0.9
        if scale != 1.0:
            zoom_level *= scale
            draw_individus()

    canvas.bind("<MouseWheel>", zoom)
    canvas.bind("<Button-4>", zoom)
    canvas.bind("<Button-5>", zoom)

    def start_pan(event):
        nonlocal pan_start_x, pan_start_y
        pan_start_x = event.x
        pan_start_y = event.y
        canvas.scan_mark(event.x, event.y)

    def do_pan(event):
        canvas.scan_dragto(event.x, event.y, gain=1)

    def end_pan(event):
        pass

    canvas.bind("<ButtonPress-1>", start_pan)
    canvas.bind("<B1-Motion>", do_pan)
    canvas.bind("<ButtonRelease-1>", end_pan)

    def on_resize(event):
        nonlocal resize_job
        if resize_job is not None:
            root.after_cancel(resize_job)
        resize_job = root.after(100, draw_individus)

    root.bind("<Configure>", on_resize)

    light_theme = {
        "bg": "white",
        "fg": "black",
        "button_bg": "lightgray",
        "button_fg": "black",
        "canvas_bg": "white",
        "node_fill": "lightblue"
    }

    dark_theme = {
        "bg": "black",
        "fg": "white",
        "button_bg": "gray",
        "button_fg": "white",
        "canvas_bg": "black",
        "node_fill": "darkblue"
    }

    current_theme = dark_theme

    def toggle_dark_mode():
        nonlocal current_theme
        if current_theme == light_theme:
            current_theme = dark_theme
        else:
            current_theme = light_theme
        apply_theme()
        draw_individus()

    menubar = tk.Menu(root)
    options_menu = tk.Menu(menubar, tearoff=0)
    options_menu.add_command(label="Toggle Dark Mode", command=toggle_dark_mode)
    menubar.add_cascade(label="Options", menu=options_menu)
    root.config(menu=menubar)

    def create_settings_popup():
        popup = tk.Toplevel(root)
        popup.title("Paramètres")
        popup.geometry("300x200")

        tk.Label(popup, text="Taille de la police des noms:").pack(pady=10)
        name_font_size_var = tk.IntVar(value=name_font_size)
        name_font_entry = tk.Entry(popup, textvariable=name_font_size_var)
        name_font_entry.pack(pady=5)

        def apply_settings():
            nonlocal name_font_size
            new_name_font_size = name_font_size_var.get()
            if new_name_font_size >= 6:
                name_font_size = new_name_font_size
                draw_individus()
                popup.destroy()
            else:
                update_status("La taille de la police des noms doit être au moins 6.", is_error=True)

        tk.Button(popup, text="Appliquer", command=apply_settings).pack(pady=10)

    options_menu.add_command(label="Paramètres", command=create_settings_popup)

    def apply_theme():
        root.configure(bg=current_theme["bg"])
        for widget in root.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=current_theme["bg"], fg=current_theme["fg"], font=('Helvetica', 10))
            elif isinstance(widget, tk.Button):
                widget.configure(bg=current_theme["button_bg"], fg=current_theme["button_fg"], font=('Helvetica', 10))
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=current_theme["canvas_bg"], fg=current_theme["fg"], font=('Helvetica', 10))
        canvas.configure(bg=current_theme["canvas_bg"])

        for arrow in canvas.find_withtag("arrow"):
            canvas.itemconfig(arrow, fill=current_theme["fg"])

    def create_individu_popup():
        popup = tk.Toplevel(root)
        popup.title("Créer Individu")
        popup.geometry("300x175")

        tk.Label(popup, text="Nom:").pack(pady=5)
        nom_entry = tk.Entry(popup, width=30)
        nom_entry.pack(pady=5)

        tk.Label(popup, text="Kill:").pack(pady=5)
        kill_entry = tk.Entry(popup, width=30)
        kill_entry.pack(pady=5)

        def submit_individu(event=None):
            nom = nom_entry.get().strip()
            kill = kill_entry.get().strip()
            if nom:
                submit_create_individu(nom, kill)
                popup.destroy()
            else:
                update_status("Le nom ne peut pas être vide.", is_error=True)

        nom_entry.bind("<Return>", submit_individu)
        kill_entry.bind("<Return>", submit_individu)

        submit_button = tk.Button(popup, text="Créer", command=submit_individu)
        submit_button.pack(pady=10)

    def submit_create_individu(nom, kill):
        nom = nom.strip().lower()
        kill = kill.strip().lower() if kill else None
        individus = fetch_data()
        existing_individu = next((ind for ind in individus if ind['nom'] == nom), None)
        if existing_individu:
            if kill:
                existing_kill = next((ind for ind in individus if ind['nom'] == kill), None)
                if existing_kill:
                    kill_id = existing_kill['id']
                else:
                    response = supabase.table('individus').insert({"nom": kill, "kill": None}).execute()
                    kill_id = response.data[0]['id']
                supabase.table('individus').update({"kill": kill_id}).eq("id", existing_individu['id']).execute()
                update_status(f"Kill de '{nom.title()}' mis à jour avec succès.")
                action_desc = f"Kill de '{nom.title()}' mis à jour vers '{kill.title()}'"
                supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
            else:
                supabase.table('individus').update({"kill": None}).eq("id", existing_individu['id']).execute()
                update_status(f"Kill de '{nom.title()}' supprimé avec succès.")
                action_desc = f"Kill de '{nom.title()}' supprimé"
                supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
            draw_individus()
        else:
            if kill:
                existing_kill = next((ind for ind in individus if ind['nom'] == kill), None)
                if existing_kill:
                    kill_id = existing_kill['id']
                else:
                    response = supabase.table('individus').insert({"nom": kill, "kill": None}).execute()
                    kill_id = response.data[0]['id']
            else:
                kill_id = None
            supabase.table('individus').insert({"nom": nom, "kill": kill_id}).execute()
            update_status(f"Individu '{nom.title()}' créé avec succès.")
            action_desc = f"Individu '{nom.title()}' créé avec kill '{kill.title() if kill else 'None'}'"
            supabase.table('log').insert({"action": action_desc, "username": current_user}).execute()
            draw_individus()

    tk.Button(root, text="Créer Individu", command=create_individu_popup, width=15).grid(row=0, column=5, padx=10, pady=5, sticky="w")

    apply_theme()
    draw_individus()

    root.mainloop()

if __name__ == "__main__":
    create_login_screen()
