import sys

with open('/root/chefport-bot/fix_images_strict.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'elif not new_url and current_url and not keep_current:' in line:
        new_lines.append('            elif not new_url and current_url and not keep_current:\n')
        # We start skipping the old logic
        skip = True
        # Add new logic
        new_lines.append('                 # Strict clear: if we dont have a better match and current is not good enough -> Clear\n')
        new_lines.append('                 action = "CLEAR"\n')
        new_lines.append('                 val = None\n')
    elif skip:
        # We are skipping the old checks until we hit the if action == line
        if 'if action == "UPDATE":' in line:
            skip = False
            new_lines.append(line)
        else:
             # Check if we are still in the indented block of the elif?
             # Actually safer to just rewrite the whole file via cat again to avoid parsing complex indentation.
             pass
    else:
        new_lines.append(line)

# Wait, parsing python indent in bash/python script is error prone.
# I will just Rewrite the file again. safer.
