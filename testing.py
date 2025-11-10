from save_editor import SaveEditor
import json
save_editor = SaveEditor()

def test():
    save_editor.selected_save_file_dict = json.load(open("backups/decompressed files/save7.hg - decompressed.json"))
    save_editor.load_bases()
    print(save_editor.get_num_components_save_file_owner())

test()