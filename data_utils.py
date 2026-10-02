# Modified in the Yuncun/ComfyUI-Prompt-Stash fork (2026-10-02): trimmed to the data-file setup.
import os
import json
import shutil
import folder_paths

file_version = "1.0"

def get_user_data_directory():
    """Get the user data directory for prompt stash files."""
    try:
        # Use ComfyUI's official get_user_directory function
        user_base = folder_paths.get_user_directory()
        user_dir = os.path.join(user_base, "prompt_stash")

        # Ensure the directory exists
        os.makedirs(user_dir, exist_ok=True)

        return user_dir
    except Exception as e:
        print(f"Warning: Could not create user directory for Prompt Stash: {e}")
        return None

def migrate_data_file_if_needed(old_base_dir, new_data_file):
    """Migrate data file from old location to new location if it exists."""
    old_data_file = os.path.join(old_base_dir, "prompt_stash_data.json")

    if os.path.exists(old_data_file) and not os.path.exists(new_data_file):
        try:
            # Copy the file to the new location
            shutil.copy2(old_data_file, new_data_file)

            # Remove the old file
            os.remove(old_data_file)

            print(f"Prompt Stash: Migrated data file from {old_data_file} to {new_data_file}")
            return True
        except Exception as e:
            print(f"Warning: Failed to migrate Prompt Stash data file: {e}")
            return False

    return False

def init_data_file(node_base_dir):
    """Initialize data file, preferring user directory with migration support."""

    # Try to get user directory first
    user_dir = get_user_data_directory()

    if user_dir:
        # Use user directory
        data_file = os.path.join(user_dir, "prompt_stash_data.json")
        default_file = os.path.join(node_base_dir, "default_prompt_stash_data.json")

        # Check if we need to migrate from old location
        migrate_data_file_if_needed(node_base_dir, data_file)

    else:
        # Fallback to node directory
        print("Prompt Stash: Using node directory as fallback for data storage")
        data_file = os.path.join(node_base_dir, "prompt_stash_data.json")
        default_file = os.path.join(node_base_dir, "default_prompt_stash_data.json")

    if not os.path.exists(data_file):
        # Create default data structure WITH VERSION
        default_data = {
            "version": file_version,
            "lists": {
                "default": {}
            }
        }

        try:
            # If default template exists, use it instead
            if os.path.exists(default_file):
                # Load default template and ensure it has version
                with open(default_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)

                # Add version if not present
                if "version" not in template_data:
                    template_data["version"] = file_version

                # Save to data file
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2)

                print(f"Prompt Stash: Initialized data file from template at {data_file}")
            else:
                # Otherwise use the minimal default data
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2)
                print(f"Prompt Stash: Created new data file at {data_file}")
        except Exception as e:
            print(f"Error initializing Prompt Stash data file: {e}")
            # If all else fails, create with minimal structure
            try:
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump({"version": file_version, "lists": {"default": {}}}, f, indent=2)
            except Exception as e2:
                print(f"Critical error: Could not create Prompt Stash data file: {e2}")
                return None
    else:
        # File exists - ensure it has version info
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add version if missing
            if "version" not in data:
                data["version"] = file_version
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                print("Prompt Stash: Added version info to existing data file")
        except Exception as e:
            print(f"Warning: Could not update data file with version info: {e}")

    return data_file

