from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.aiff import AIFF
from mutagen.id3 import ID3, TCON
import sqlite3
import os
import tkinter as tk
from tkinter import *
from tkinter import ttk
import sv_ttk
import pyperclip
from AutoEntry import AutocompleteEntry
import Local_Vars

db_path = Local_Vars.DATABASE_PATH
if not os.path.exists(db_path):
    db_path = Local_Vars.DATABASE_PATH_HOME_PC

local_tracks_folder_path = Local_Vars.ALL_TRACKS_PATH

xpad = 5
ypad = 5

root = tk.Tk()
root.title(Local_Vars.GUI_TITLE)
sv_ttk.set_theme("dark")

# Configure the root window's columns
root.grid_columnconfigure(0, weight=1)  # Left column
root.grid_columnconfigure(1, weight=1)  # Center column
root.grid_columnconfigure(2, weight=1)  # Right column

class Orso_Tag_Editor:
    """Class to edit audio tags using the mutagen library."""
    
    def __init__(self, inp_db_path):
        self.db_path = inp_db_path
        self.database_col_headers = ['file_path', 'track_title', 'genre']
        self.conn = None
        self.cursor = None
        self.connect_to_db()

    def __exit__(self, exc_type, exc_value, traceback):
        # print("\nInside __exit__")
        # print("\nExecution type:", exc_type)
        # print("\nExecution value:", exc_value)
        # print("\nTraceback:", traceback)
        self.connection.close()

    def connect_to_db(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def display_tag_db(self):

        #clear the window if it exists and is not empty
        for widget in root.winfo_children():
            widget.destroy()
        
        frame_row_index = 0
        frame_col_index = 1

        '''EDIT DATA FRAME'''
        # create the edit data frame that contains a "track title label widget" and a "genre entry widget"
        self.edit_data_label_widgets = {}
        self.edit_data_entry_widgets = {}
        self.edit_data_frame = ttk.Frame(root)
        
        # create the label and entry widgets, these will be populated when a row is selected in the treeview
        self.track_file_path_label = ttk.Label(self.edit_data_frame, text="Track File Path", relief="solid", borderwidth=1)
        self.track_file_path_label.grid(row=0, column=0, padx=xpad, pady=ypad)
        
        # self.track_genre_entry.insert(0, "New Genre")
        self.edit_data_label_widgets['File Path'] = self.track_file_path_label

        self.track_genre_entry = ttk.Entry(self.edit_data_frame)
        # self.track_genre_entry.build(self.create_genre_master_list(), 5, True, no_results_message=None)
        self.track_genre_entry.grid(row=0, column=1, padx=xpad, pady=ypad)
        # Make the entry widget select all text when clicked
        self.track_genre_entry.bind("<FocusIn>", self.select_all)
        
        self.edit_data_entry_widgets['Genre'] = self.track_genre_entry

        # self.track_genre_entry = AutocompleteEntry(self.edit_data_frame)
        # self.track_genre_entry.build(self.create_genre_master_list(), 5, True, no_results_message=None)
        # self.track_genre_entry.grid(row=0, column=1, padx=xpad, pady=ypad)
        # self.edit_data_entry_widgets['Genre'] = self.track_genre_entry

        self.edit_data_frame.grid(row=frame_row_index, column=frame_col_index, padx=xpad, pady=ypad)

        frame_row_index += 1
        
        '''SEARCH FRAME'''
        # create the search frame that contains a "search label widget" and a "search entry widget"
        self.search_entry_dict = {}
        self.search_frame = ttk.Frame(root)

        self.search_label_widget = ttk.Label(self.search_frame, text=f'Search By Title', relief="solid", borderwidth=1)
        self.search_label_widget.grid(row=0, column=0, padx=xpad, pady=ypad)
        
        self.search_entry_widget = ttk.Entry(self.search_frame)
        self.search_entry_widget.grid(row=0, column=1, padx=xpad, pady=ypad)
        self.search_entry_widget.bind('<KeyRelease>', self.filter_tree_rows)
        self.search_entry_dict['Search'] = self.search_entry_widget
        
        self.search_frame.grid(row=frame_row_index, column=frame_col_index, padx=xpad, pady=ypad)
        frame_row_index += 1

        """TREEVIEW FRAME"""
        # print("Displaying tags in the database...")
        # create the treeview widget from the database
        self.treeview_data_frame = ttk.Frame(root)
        self.track_data_treeview = ttk.Treeview(self.treeview_data_frame, columns=self.database_col_headers, show='headings')
        for column in self.database_col_headers:
            self.track_data_treeview.heading(column, text=column)
            text_len = len(column)
            col_w = text_len * 21
            self.track_data_treeview.column(column, width=col_w, anchor='center')
        self.track_data_treeview.grid(row=0, column=0, sticky="nsew")
        self.track_data_treeview.bind('<<TreeviewSelect>>', self.treeview_on_select)
        self.treeview_data_frame.grid(row=frame_row_index, column=frame_col_index, sticky="nsew", padx=xpad, pady=ypad)
        frame_row_index += 1
        self.populate_treeview()

        '''BUTTON FRAME'''
        # create the button frame that contains a "commit changes" button
        btn_fram_col_index = 0
        self.buttons_frame = Frame(root)
        self.reload_button = ttk.Button(self.buttons_frame, text="Reload Database", command=lambda: self.reload_treeview())
        self.reload_button.grid(column=btn_fram_col_index, row=1, padx=xpad, pady=ypad)
        btn_fram_col_index += 1

        self.commit_changes_button = ttk.Button(self.buttons_frame, text="Commit Changes", command=lambda: self.commit_changes_to_db())
        self.commit_changes_button.grid(column=btn_fram_col_index, row=1, padx=xpad, pady=ypad)
        btn_fram_col_index += 1

        if os.path.exists(local_tracks_folder_path):
            self.update_file_tags_button = ttk.Button(self.buttons_frame, text="Update File Tags", command=lambda: self.commit_db_changes_to_files())
            self.update_file_tags_button.grid(column=btn_fram_col_index, row=1, padx=xpad, pady=ypad)
            btn_fram_col_index += 1

            self.add_tracks_button = ttk.Button(self.buttons_frame, text="Add Tracks to DB", command=lambda: self.add_tracks_to_db())
            self.add_tracks_button.grid(column=btn_fram_col_index, row=1, padx=xpad, pady=ypad)
            btn_fram_col_index += 1

        self.data_base_row_count_label = ttk.Label(self.buttons_frame, text=f"Database Row Count: {len(self.get_db_data())}")
        self.data_base_row_count_label.grid(column=btn_fram_col_index, row=1, padx=xpad, pady=ypad)
        btn_fram_col_index += 1

        self.buttons_frame.grid(row=frame_row_index, column=frame_col_index, padx=xpad, pady=ypad)
        
        '''Genre MASTER LIST FRAME'''
        # create a treeview widget to display the genre master list 
        self.genre_master_list_frame = ttk.Frame(root, borderwidth=2, relief="solid")

        self.genre_master_list_treeview = ttk.Treeview(self.genre_master_list_frame, columns=['Genre'], show='headings')
        self.genre_master_list_treeview.heading('Genre', text='Genres', anchor='center')
        self.genre_master_list_treeview.bind('<<TreeviewSelect>>', self.genre_treeview_on_select)
        self.populate_genre_master_list()

        self.genre_master_list_treeview.grid(row=0, column=0, sticky="nsew")

        # Add these two lines to make the treeview expand with the frame
        self.genre_master_list_frame.grid_rowconfigure(0, weight=1)
        self.genre_master_list_frame.grid_columnconfigure(0, weight=1)

        treeview_data_frame_row = self.treeview_data_frame.grid_info()['row']
        treeview_data_frame_height = self.track_data_treeview.winfo_height()
        self.genre_master_list_treeview.config(height=35)

        #create copy genre master list to clipboard button
        self.copy_genre_button = ttk.Button(self.genre_master_list_frame, text="Copy All Genres to Clipboard", command=lambda: self.copy_genre_masterlist_to_clipboard())
        self.copy_genre_button.grid(row=1, column=0, padx=xpad, pady=ypad)

        self.genre_master_list_frame.grid(row=treeview_data_frame_row, column=frame_col_index+1, padx=xpad, pady=ypad, sticky="nsew")

        # make root window maximized
        root.state('zoomed')
        root.mainloop()

    def select_all(self, event):
        event.widget.select_range(0, tk.END)
        event.widget.icursor(tk.END)
        return 'break'

    def add_tracks_to_db(self):
        """Add tracks from a folder to the SQLite database."""

        self.cursor.execute('''
            DROP TABLE IF EXISTS tracks
        ''')
        # Create table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                file_path TEXT PRIMARY KEY,
                track_title TEXT,
                genre TEXT
            )
        ''')

        loop_count = 0
        # loop_limit = 1000
        for root, dirs, files in os.walk(local_tracks_folder_path):
            for file in files:
                # if loop_count > loop_limit:
                #     break
                file_path = os.path.join(root, file)
                tags_to_return = ["title", "genre"]
                returned_tags = return_tags(file_path, tags_to_return)
                title_tag_key = "TIT2" if os.path.splitext(file_path)[1].lower() == ".aiff" else "title"
                genre_tag_key = "TCON" if os.path.splitext(file_path)[1].lower() == ".aiff" else "genre"
                try:
                    # Insert or update the track in the database
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO tracks (file_path, track_title, genre)
                        VALUES (?, ?, ?)
                    ''', (file_path, returned_tags.get(title_tag_key, "Unknown"), returned_tags.get(genre_tag_key, "Unknown")))

                    loop_count += 1

                    # print(f"Added/Updated track: {file_path}")
                    # print(f"Title: {returned_tags.get(title_tag_key, 'Unknown')}")
                    # print(f"Genre: {returned_tags.get(genre_tag_key, 'Unknown')}")
                except Exception as e:
                    continue
        print(f"\nAdded/Updated {loop_count} tracks to the database.")
        self.conn.commit()
        self.display_tag_db()
    
    def filter_tree_rows(self, event=None):
        lookup_title = self.search_entry_dict['Search'].get()
        
        self.delete_tree_rows()

        # Configure alternating row colors
        self.track_data_treeview.tag_configure("even", background="#000000")  # Black
        self.track_data_treeview.tag_configure("odd", background="#151525")   # Dark Blue

        # Re-insert the items that match the filter
        match_count = 0
        for row in self.get_db_data():
            if lookup_title.lower() in row[1].lower(): 
                match_count += 1
                # Apply "even" or "odd" tag based on the row index
                tag = "even" if match_count % 2 == 0 else "odd"
                self.track_data_treeview.insert('', 'end', values=row, tags=(tag,))

        self.resize_treeview()

    def delete_tree_rows(self):
        # Delete all items in the Treeview
        for item in self.track_data_treeview.get_children():
            self.track_data_treeview.delete(item)

    def delete_genre_tree_rows(self):
        # Delete all items in the Genre Master List Treeview
        for item in self.genre_master_list_treeview.get_children():
            self.genre_master_list_treeview.delete(item)

    def load_track_edit_data(self, val_list):
        # print(f"Loading track edit data for: {val_list}")
        # print(f"Track title: {val_list[1]}")
        # print(f"Track genre: {val_list[2]}")
        self.edit_data_label_widgets['File Path'].config(text=val_list[0])

        self.edit_data_entry_widgets['Genre'].delete(0, tk.END)
        self.edit_data_entry_widgets['Genre'].insert(0, val_list[2])

    def auto_complete_genre(self, event=None):
        """Auto-complete the genre entry field based on the genre master list."""
        # Get the current text in the genre entry field
        current_text = self.edit_data_entry_widgets['Genre'].get()
        # print(f"Current text: {current_text}")

        if not current_text:
            return
        
        # Get the list of genres from the genre master list
        genre_list = self.create_genre_master_list()

        # Find matching genres
        matching_genres = [genre for genre in genre_list if genre.lower().startswith(current_text.lower())]

        # If there's a match, show the first one in the entry field without deleting the current text
        # if matching_genres:

        # if matching_genres:
        #     self.edit_data_entry_widgets['Genre'].delete(0, tk.END)
        #     self.edit_data_entry_widgets['Genre'].insert(0, matching_genres[0])

    def copy_genre_masterlist_to_clipboard(self):
        genre_master_list = self.create_genre_master_list()
        # put genre master list into a string
        genre_master_list_str = "\n".join(genre_master_list)
        #copy to clipboard
        pyperclip.copy(genre_master_list_str)

    def genre_treeview_on_select(self, event):
        try:
            selected = self.genre_master_list_treeview.selection()[0]
        except IndexError:
            return
        #copy to clipboard
        values = self.genre_master_list_treeview.item(selected, 'values')
        # print(values)
        genre = values[0]
        # print(f"Selected genre: {genre}")
        pyperclip.copy(genre)

    def treeview_on_select(self, event):
        try:
            selected = self.track_data_treeview.selection()[0]
        except IndexError:
            return
        values = self.track_data_treeview.item(selected, 'values')
        # print(values)  
        self.load_track_edit_data(values)

    def reload_treeview(self):
        # print("Reloading treeview...")
        self.delete_tree_rows()
        self.populate_treeview()

        self.delete_genre_tree_rows()
        self.populate_genre_master_list()
        self.filter_tree_rows()

    def populate_genre_master_list(self):
        # print("Populating genre master list...")
         # Configure alternating row colors
        self.genre_master_list_treeview.tag_configure("even", background="#000000")  # Black
        self.genre_master_list_treeview.tag_configure("odd", background="#151525")   # Dark Blue

        max_col_length = 0
        for index, row in enumerate(self.create_genre_master_list()):
            local_max_col_length = 0
            # print(row)
            local_max_col_length = max(local_max_col_length, len(row))
            max_col_length = max(max_col_length, local_max_col_length)
            
            # Apply "even" or "odd" tag based on the row index
            tag = "even" if index % 2 == 0 else "odd"
            self.genre_master_list_treeview.insert('', 'end', values=(row,), tags=(tag,))

        # # Set the width of the first column based on the max_col_length
        self.genre_master_list_treeview.column('Genre', width=max_col_length * 20, anchor='center')

    def create_genre_master_list(self):
        """Create a master list of genres from the database."""
        self.cursor.execute('SELECT DISTINCT genre FROM tracks')
        rows = self.cursor.fetchall()
        # print(f"Genre List Rows: {rows}")
        genre_list = [row[0] for row in rows]
        # genre_list = list(set(genre_list))
        genre_list.sort()
        # print(f"\nGenre list: {genre_list}")
        return genre_list
    
    def populate_treeview(self):
        """Populate the treeview with data from the database."""
        # print("Populating treeview with data from the database...")

        # Configure alternating row colors
        self.track_data_treeview.tag_configure("even", background="#000000")  # Black
        self.track_data_treeview.tag_configure("odd", background="#151525")   # Dark Blue

        max_col_length = 0
        for index, row in enumerate(self.get_db_data()):
            local_max_col_length = 0
            for col in row:
                if isinstance(col, str):
                    local_max_col_length = max(local_max_col_length, len(col))
            max_col_length = max(max_col_length, local_max_col_length)

            # Apply "even" or "odd" tag based on the row index
            tag = "even" if index % 2 == 0 else "odd"
            self.track_data_treeview.insert('', 'end', values=row, tags=(tag,))

        # Set the width of the first column based on the max_col_length
        self.track_data_treeview.column(self.database_col_headers[0], width=max_col_length * 7, anchor='center')

        self.resize_treeview()

    def get_db_data(self):
        """Get all data from the database."""
        try:
            self.cursor.execute('SELECT * FROM tracks')
            rows = self.cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            print(f"Error fetching data from database: {e}")
            return []
        
    def resize_treeview(self):
        self.track_data_treeview.config(height=min(len(self.track_data_treeview.get_children()), 35))

    def commit_changes_to_db(self):
        """Commit changes to the database."""
        # print("Committing changes to the database...")
        # check all the entry boxes within the data_frame for non-empty values
        file_path = self.edit_data_label_widgets['File Path'].cget("text")
        new_genre = self.edit_data_entry_widgets['Genre'].get()
        if not file_path or not new_genre:
            #make GUI flash

            print("Please select a track and enter a genre.")
            return
        
        self.update_genre_in_db(file_path, new_genre)
        self.conn.commit()
        self.reload_treeview()
    
    def update_genre_in_db(self, file_path, new_genre):
        """Update the genre in the database."""
        try:
            # Update the genre in the database
            self.cursor.execute('''
                UPDATE tracks
                SET genre = ?
                WHERE file_path = ?
            ''', (new_genre, file_path))
            print(f"Updated DATABASE genre to '{new_genre}' for file: {file_path}")
        except sqlite3.Error as e:
            print(f"Error updating genre in database: {e}")
        # Update the genre in the audio file

    def commit_db_changes_to_files(self):
        """Commit changes to the audio files."""
        # print("Committing changes to audio files...")
        for row in self.get_db_data():
            file_path = row[0]
            new_genre = row[2]
            file_current_genre = return_genre(file_path)
            if file_current_genre == new_genre:
                continue
            
            update_genre(file_path, new_genre)
            print(f"Updated genre to '{new_genre}' for file: {file_path}")
    
def return_audio_object(file_path):
    """Return the audio object based on the file type."""
    file_type = os.path.splitext(file_path)[1].lower()
    try:
        if file_type == ".mp3":
            return EasyID3(file_path)
        elif file_type == ".flac":
            return FLAC(file_path)
        elif file_type == ".aiff":
            return AIFF(file_path)
        else:
            return None
    except Exception as e:
        print(f"Error reading audio file: {e}")
        return None
    
def display_tags(file_path):
    """Display all tags of an audio file."""
    audio = return_audio_object(file_path)
    if audio is None:
        print("Unsupported file type. Please provide a .mp3, .flac, or .aiff file.")
        return
    
    print(f"Tags for {file_path}:")

    for tag, value in audio.items():
        if isinstance(value, list):
            value = ', '.join(value)
        print(f"{tag}: {value}")
            
def display_genre(file_path):
    """Display the genre tag of an audio file."""
    file_type = os.path.splitext(file_path)[1].lower()
    audio = return_audio_object(file_path)
    if audio is None:
        print("Unsupported file type. Please provide a .mp3, .flac, or .aiff file.")
        return
    try:
        if file_type == ".mp3" or file_type == ".flac":
            print(f"Genre: {audio.get('genre', ['Unknown'])[0]}")
        elif file_type == ".aiff":
            print(f"Genre: {audio.get('TCON', ['Unknown'])[0]}")
    except Exception as e:
        print(f"Error reading genre: {e}")

def return_genre(file_path):
    """Return the genre tag of an audio file."""
    file_type = os.path.splitext(file_path)[1].lower()
    audio = return_audio_object(file_path)
    if audio is None:
        print("Unsupported file type. Please provide a .mp3, .flac, or .aiff file.")
        return
    if file_type == ".mp3" or file_type == ".flac":
        return audio.get('genre', ['Unknown'])[0]
    elif file_type == ".aiff":
        return audio.get('TCON', ['Unknown'])[0]
    
def return_tags(file_path, tag_list_to_return):
    """Display the genre tag of an audio file."""
    file_type = os.path.splitext(file_path)[1].lower()
    audio = return_audio_object(file_path)
    if audio is None:
        print(fr"Unsupported file type [{file_type}]. Please provide a .mp3, .flac, or .aiff file.")
        return
    tag_dict = {}
    if file_type == ".aiff":
        audio = AIFF(file_path)
        if "genre" in tag_list_to_return:
            tag_list_to_return.remove("genre")
            tag_list_to_return.append("TCON")
        if "title" in tag_list_to_return:
            tag_list_to_return.remove("title")
            tag_list_to_return.append("TIT2")

    for tag in tag_list_to_return:
        if tag in audio:
            tag_dict[tag] = audio[tag][0]
        else:
            tag_dict[tag] = "Unknown"
    return tag_dict

def update_genre(file_path, new_genre):
    """Update the genre tag of an audio file."""
    audio = return_audio_object(file_path)
    if audio is None:
        print("Unsupported file type. Please provide a .mp3, .flac, or .aiff file.")
        return
    file_type = os.path.splitext(file_path)[1].lower()

    if file_type == ".mp3" or file_type == ".flac":
        audio["genre"] = new_genre
        audio.save()
        # print(f"Updated genre to '{new_genre}' for MP3 or Flac file: {file_path}")
    elif file_type == ".aiff":
        audio["TCON"] = TCON(encoding=3, text=[new_genre])  # Use TCON frame for genre
        audio.save()
        # print(f"Updated genre to '{new_genre}' for AIFF file: {file_path}")

def add_tracks_to_db(db_path, folder_path):
    """Add tracks from a folder to the SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        DROP TABLE IF EXISTS tracks
    ''')
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            file_path TEXT PRIMARY KEY,
            track_title TEXT,
            genre TEXT
        )
    ''')

    loop_count = 0
    # loop_limit = 1000
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # if loop_count > loop_limit:
            #     break
            file_path = os.path.join(root, file)
            tags_to_return = ["title", "genre"]
            returned_tags = return_tags(file_path, tags_to_return)
            title_tag_key = "TIT2" if os.path.splitext(file_path)[1].lower() == ".aiff" else "title"
            genre_tag_key = "TCON" if os.path.splitext(file_path)[1].lower() == ".aiff" else "genre"
            try:
                # Insert or update the track in the database
                cursor.execute('''
                    INSERT OR REPLACE INTO tracks (file_path, track_title, genre)
                    VALUES (?, ?, ?)
                ''', (file_path, returned_tags.get(title_tag_key, "Unknown"), returned_tags.get(genre_tag_key, "Unknown")))

                loop_count += 1

                # print(f"Added/Updated track: {file_path}")
                # print(f"Title: {returned_tags.get(title_tag_key, 'Unknown')}")
                # print(f"Genre: {returned_tags.get(genre_tag_key, 'Unknown')}")
            except Exception as e:
                continue
    print(f"\nAdded/Updated {loop_count} tracks to the database.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    ####GUI Testing####
    def display_gui():
        tag_editor_gui = Orso_Tag_Editor(db_path)
        tag_editor_gui.display_tag_db()

    display_gui()
