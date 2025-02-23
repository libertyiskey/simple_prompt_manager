import streamlit as st
import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend/src"))
from prompt_manager_core import PromptManager
from datetime import datetime
import sqlite3

# Must be the first Streamlit command
st.set_page_config(page_title="Prompt & Folder Manager", layout="wide")

# Initialize the PromptManager instance
@st.cache_resource
def get_prompt_manager():
    return PromptManager()

pm = get_prompt_manager()

# -----------------------------
# Streamlit App Interface
# -----------------------------
st.title("Prompt & Folder Manager")

# Initialize session state for navigation if not exists
if 'navigation' not in st.session_state:
    st.session_state['navigation'] = "Add Prompt"
if 'selected_folder' not in st.session_state:
    st.session_state['selected_folder'] = None
if 'selected_prompt_id' not in st.session_state:
    st.session_state['selected_prompt_id'] = None
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = "list"  # can be "list" or "single"

# Sidebar navigation
st.sidebar.title("Navigation")

# Main menu options with icons
if st.sidebar.button("➕ Add Prompt", use_container_width=True):
    st.session_state['navigation'] = "Add Prompt"
    st.session_state['view_mode'] = "list"
    st.session_state['selected_prompt_id'] = None
if st.sidebar.button("📝 Manage Prompts", use_container_width=True):
    st.session_state['navigation'] = "Manage Prompts"
    st.session_state['view_mode'] = "list"
    st.session_state['selected_prompt_id'] = None
if st.sidebar.button("📁 Manage Folders", use_container_width=True):
    st.session_state['navigation'] = "Manage Folders"
    st.session_state['view_mode'] = "list"
    st.session_state['selected_prompt_id'] = None

# Display folders in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📂 Folders")

# Get all prompts and folders
all_prompts = pm.get_prompts()
folders = pm.get_folders()
folder_mapping = pm.get_folder_mapping()

# Add "Uncategorized" section
uncategorized_prompts = [p for p in all_prompts if p["folder_id"] is None]
if uncategorized_prompts:
    with st.sidebar.expander("📁 Uncategorized"):
        for prompt in uncategorized_prompts:
            if st.button(f"📄 {prompt['title']}", key=f"prompt_{prompt['id']}", use_container_width=True):
                st.session_state['navigation'] = "Manage Prompts"
                st.session_state['selected_folder'] = None
                st.session_state['selected_prompt_id'] = prompt['id']
                st.session_state['view_mode'] = "single"

# Display folders and their prompts
if folders:
    for folder in folders:
        with st.sidebar.expander(f"📁 {folder['name']}"):
            if st.button(f"📂 Show all in {folder['name']}", key=f"folder_{folder['id']}", use_container_width=True):
                st.session_state['navigation'] = "Manage Prompts"
                st.session_state['selected_folder'] = folder['id']
                st.session_state['selected_prompt_id'] = None
                st.session_state['view_mode'] = "list"
            
            folder_prompts = [p for p in all_prompts if p["folder_id"] == folder['id']]
            if folder_prompts:
                st.markdown("---")
                for prompt in folder_prompts:
                    if st.button(f"📄 {prompt['title']}", key=f"prompt_{folder['id']}_{prompt['id']}", use_container_width=True):
                        st.session_state['navigation'] = "Manage Prompts"
                        st.session_state['selected_folder'] = folder['id']
                        st.session_state['selected_prompt_id'] = prompt['id']
                        st.session_state['view_mode'] = "single"
            else:
                st.caption("No prompts in this folder")
else:
    st.sidebar.info("No folders created yet")

# Initialize session states if not exists
if 'expanded_prompt_id' not in st.session_state:
    st.session_state['expanded_prompt_id'] = None

choice = st.session_state['navigation']

# -----------------------------
# Add Prompt Section
# -----------------------------
if choice == "Add Prompt":
    st.subheader("Add a New Prompt")
    
    # Replace expandable with simple info message
    st.info("💡 You can reference other prompts in your content using `{{prompt_id}}` or `{{prompt_title}}`.\nFor example: `{{1}}` or `{{My Prompt Title}}`")
    
    title = st.text_input("Prompt Title")
    content = st.text_area("Prompt Content", height=200,
                          help="Reference other prompts using {{prompt_id}} or {{prompt_title}}")
    
    # Preview section to show resolved content
    if content:
        with st.expander("👁️ Preview with Resolved References", expanded=True):
            resolved_content = pm.resolve_prompt_references(content)
            st.markdown("```\n" + resolved_content + "\n```")
    
    # Folder selection: "None" means no folder selected (value is None)
    folder_options = [("None", None)] + [(name, fid) for fid, name in folder_mapping.items()]
    selected_index = st.selectbox("Select Folder (optional)", range(len(folder_options)),
                                  format_func=lambda x: folder_options[x][0])
    selected_folder = folder_options[selected_index][1]
    if st.button("Add Prompt"):
        if title.strip() and content.strip():
            try:
                pm.add_prompt(title.strip(), content.strip(), selected_folder)
                st.success("Prompt added successfully!")
                st.rerun()
            except sqlite3.Error as e:
                st.error(str(e))
        else:
            st.error("Both title and content are required.")

# -----------------------------
# Manage Prompts Section
# -----------------------------
elif choice == "Manage Prompts":
    if st.session_state['view_mode'] == "single" and st.session_state['selected_prompt_id'] is not None:
        # Single prompt view
        prompt = pm.get_prompt(st.session_state['selected_prompt_id'])
        if prompt:
            # Back button
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if st.button("← Back to List"):
                    st.session_state['view_mode'] = "list"
                    st.session_state['selected_prompt_id'] = None
                    st.rerun()
            
            # Prompt display and edit form
            edit_key = f"edit_prompt_{prompt['id']}"
            if st.session_state.get(edit_key, False):
                # Edit mode
                with st.form(key=f"form_prompt_single_{prompt['id']}"):
                    # Add available prompts reference
                    with st.expander("📑 Available Prompts for Reference"):
                        st.markdown("""
                        You can reference other prompts in your content using `{{prompt_id}}` or `{{prompt_title}}`.
                        For example: `{{1}}` or `{{My Prompt Title}}`
                        
                        Available prompts:
                        """)
                        for p in all_prompts:
                            if p['id'] != prompt['id']:  # Don't show current prompt
                                st.markdown(f"- ID: `{{`{p['id']}`}}` - Title: `{{`{p['title']}`}}`")
                    
                    st.text_input("Title", value=prompt['title'], key="title_input")
                    if prompt['folder_id']:
                        folder_name = folder_mapping.get(prompt['folder_id'], "Unknown")
                        st.markdown(f"*Currently in folder: 📁 {folder_name}*")
                    
                    edit_folder_options = [("None", None)] + [(name, fid) for fid, name in folder_mapping.items()]
                    new_selected_index = st.selectbox("Move to Folder", range(len(edit_folder_options)),
                                                      format_func=lambda x: edit_folder_options[x][0],
                                                      index=0 if prompt['folder_id'] is None else
                                                      [fid for fid, name in folder_mapping.items()].index(prompt['folder_id']) + 1)
                    new_folder = edit_folder_options[new_selected_index][1]
                    
                    st.markdown("### Content")
                    new_content = st.text_area("Prompt Content", value=prompt['content'], height=300,
                                             help="You can reference other prompts using {{prompt_id}} or {{prompt_title}}",
                                             label_visibility="collapsed")
                    
                    # Preview section
                    if new_content:
                        with st.expander("👁️ Preview with Resolved References", expanded=True):
                            resolved_content = pm.resolve_prompt_references(new_content)
                            st.markdown("```\n" + resolved_content + "\n```")
                    
                    # Action buttons in form
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
                        if submitted:
                            new_title = st.session_state.title_input
                            if new_title.strip() and new_content.strip():
                                try:
                                    if pm.update_prompt(prompt['id'], new_title.strip(), new_content.strip(), new_folder):
                                        st.success("Prompt updated!")
                                        st.session_state[edit_key] = False
                                        st.rerun()
                                except sqlite3.Error as e:
                                    st.error(str(e))
                            else:
                                st.error("Both title and content are required for update.")
                    with col2:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            st.session_state[edit_key] = False
                            st.rerun()
            else:
                # Display mode
                st.markdown(f"# 📄 {prompt['title']}")
                if prompt['folder_id']:
                    folder_name = folder_mapping.get(prompt['folder_id'], "Unknown")
                    st.markdown(f"*In folder: 📁 {folder_name}*")
                
                st.markdown("### Content")
                st.markdown(f"```\n{prompt['content']}\n```")
                
                # Actions
                col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
                with col1:
                    if st.button("✏️ Edit", key=f"btn_edit_single_{prompt['id']}", use_container_width=True):
                        st.session_state[f"edit_prompt_{prompt['id']}"] = True
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"btn_del_single_{prompt['id']}", use_container_width=True):
                        if pm.delete_prompt(prompt['id']):
                            st.success("Prompt deleted!")
                            st.session_state['view_mode'] = "list"
                            st.session_state['selected_prompt_id'] = None
                            st.rerun()
                with col3:
                    preview_key = f"preview_prompt_{prompt['id']}"
                    if st.button("👁️ Preview", key=f"btn_preview_single_{prompt['id']}", use_container_width=True):
                        st.session_state[preview_key] = not st.session_state.get(preview_key, False)
                
                # Show preview if button is clicked
                preview_key = f"preview_prompt_{prompt['id']}"
                if st.session_state.get(preview_key, False):
                    st.markdown("### Preview with Resolved References")
                    resolved_content = pm.resolve_prompt_references(prompt['content'])
                    st.markdown("```\n" + resolved_content + "\n```")
                
                # Version history section
                st.markdown("---")
                st.markdown("### 📚 Version History")
                versions = pm.get_prompt_versions(prompt['id'])
                
                # Create columns for version list and version preview
                ver_col1, ver_col2 = st.columns([1, 2])
                
                with ver_col1:
                    st.markdown("#### Versions")
                    # Initialize version preview state if not exists
                    if 'preview_version' not in st.session_state:
                        st.session_state['preview_version'] = None
                    
                    for version in versions:
                        version_date = datetime.strptime(version['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
                        is_current = version['version_number'] == prompt['current_version']
                        
                        # Create a container for each version with better styling
                        with st.container():
                            version_label = f"v{version['version_number']} - {version_date}"
                            if is_current:
                                version_label += " (current)"
                            if st.button(version_label, 
                                       key=f"ver_{prompt['id']}_{version['version_number']}", 
                                       use_container_width=True):
                                st.session_state['preview_version'] = version['version_number']
                
                with ver_col2:
                    st.markdown("#### Version Details")
                    if st.session_state['preview_version']:
                        preview_version = pm.get_prompt_version(prompt['id'], st.session_state['preview_version'])
                        if preview_version:
                            st.markdown(f"**Title:** {preview_version['title']}")
                            if preview_version['folder_id']:
                                folder_name = folder_mapping.get(preview_version['folder_id'], "Unknown")
                                st.markdown(f"*Folder: 📁 {folder_name}*")
                            st.markdown("**Content:**")
                            st.markdown(f"```\n{preview_version['content']}\n```")
                            
                            # Show resolved preview for this version
                            with st.expander("👁️ Preview with Resolved References"):
                                resolved_content = pm.resolve_prompt_references(preview_version['content'])
                                st.markdown(f"```\n{resolved_content}\n```")
                            
                            # Only show restore button if not current version
                            if preview_version['version_number'] != prompt['current_version']:
                                if st.button("🔄 Restore this version", use_container_width=True):
                                    if pm.restore_version(prompt['id'], preview_version['version_number']):
                                        st.success("Version restored successfully!")
                                        st.rerun()
                    else:
                        st.info("Select a version to view details")
    else:
        # List view - keep existing list view code
        if st.session_state['selected_folder'] is None:
            st.subheader("All Prompts")
            # Folder filter
            filter_options = [("All", None)] + [(name, fid) for fid, name in folder_mapping.items()]
            selected_filter_index = st.selectbox("Filter by Folder", range(len(filter_options)),
                                                 format_func=lambda x: filter_options[x][0],
                                                 index=0)
            filter_folder = filter_options[selected_filter_index][1]
            prompts = pm.get_prompts(folder_id=filter_folder)
        else:
            folder_name = folder_mapping.get(st.session_state['selected_folder'], "Uncategorized")
            st.subheader(f"📁 {folder_name}")
            prompts = pm.get_prompts(folder_id=st.session_state['selected_folder'])

        # Search functionality with better styling
        st.markdown("---")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("🔍 Search prompts by title", placeholder="Type to search...")
        with search_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Clear Search", use_container_width=True):
                search_query = ""

        if search_query:
            prompts = [p for p in prompts if search_query.lower() in p['title'].lower()]

        # Display prompts
        if prompts:
            for prompt in prompts:
                with st.container():
                    edit_key = f"edit_prompt_{prompt['id']}"
                    if st.session_state.get(edit_key, False):
                        # Edit mode
                        with st.form(key=f"form_prompt_{prompt['id']}"):
                            st.text_input("Title", value=prompt['title'], key=f"title_input_{prompt['id']}")
                            if prompt['folder_id']:
                                folder_name = folder_mapping.get(prompt['folder_id'], "Unknown")
                                st.markdown(f"*Currently in folder: 📁 {folder_name}*")
                            
                            edit_folder_options = [("None", None)] + [(name, fid) for fid, name in folder_mapping.items()]
                            new_selected_index = st.selectbox("Move to Folder", range(len(edit_folder_options)),
                                                                  format_func=lambda x: edit_folder_options[x][0],
                                                                  index=0 if prompt['folder_id'] is None else
                                                                  [fid for fid, name in folder_mapping.items()].index(prompt['folder_id']) + 1)
                            new_folder = edit_folder_options[new_selected_index][1]
                            
                            new_content = st.text_area("Prompt Content", value=prompt['content'], height=150, label_visibility="collapsed")
                            
                            # Action buttons in form
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
                                if submitted:
                                    new_title = st.session_state[f"title_input_{prompt['id']}"]
                                    if new_title.strip() and new_content.strip():
                                        try:
                                            if pm.update_prompt(prompt['id'], new_title.strip(), new_content.strip(), new_folder):
                                                st.success("Prompt updated!")
                                                st.session_state[edit_key] = False
                                                st.rerun()
                                        except sqlite3.Error as e:
                                            st.error(str(e))
                                    else:
                                        st.error("Both title and content are required for update.")
                            with col2:
                                if st.form_submit_button("❌ Cancel", use_container_width=True):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                    else:
                        # Display mode
                        # Header with title
                        header_col1, header_col2 = st.columns([3, 1])
                        with header_col1:
                            st.markdown(f"### 📄 {prompt['title']}")
                        with header_col2:
                            st.markdown(f"<div style='text-align: right; color: gray; padding-top: 10px;'>ID: {prompt['id']}</div>", 
                                      unsafe_allow_html=True)
                        
                        # Content section
                        st.markdown(f"```\n{prompt['content']}\n```")
                        
                        # Actions row
                        action_col1, action_col2, action_col3, action_col4 = st.columns([1, 1, 1, 3])
                        with action_col1:
                            if st.button("✏️ Edit", key=f"btn_edit_{prompt['id']}", use_container_width=True):
                                st.session_state[f"edit_prompt_{prompt['id']}"] = True
                                st.rerun()
                        with action_col2:
                            if st.button("🗑️ Delete", key=f"btn_del_{prompt['id']}", use_container_width=True):
                                if pm.delete_prompt(prompt['id']):
                                    st.success("Prompt deleted!")
                                    st.rerun()
                        with action_col3:
                            preview_key = f"preview_prompt_{prompt['id']}"
                            if st.button("👁️ Preview", key=f"btn_preview_{prompt['id']}", use_container_width=True):
                                st.session_state[preview_key] = not st.session_state.get(preview_key, False)
                        
                        # Show preview if button is clicked
                        preview_key = f"preview_prompt_{prompt['id']}"
                        if st.session_state.get(preview_key, False):
                            st.markdown("### Preview with Resolved References")
                            resolved_content = pm.resolve_prompt_references(prompt['content'])
                            st.markdown("```\n" + resolved_content + "\n```")
                        
                        # Version history section
                        st.markdown("---")
                        st.markdown("### 📚 Version History")
                        versions = pm.get_prompt_versions(prompt['id'])
                        
                        # Create columns for version list and version preview
                        ver_col1, ver_col2 = st.columns([1, 2])
                        
                        with ver_col1:
                            st.markdown("#### Versions")
                            # Initialize version preview state if not exists
                            if 'preview_version' not in st.session_state:
                                st.session_state['preview_version'] = None
                            
                            for version in versions:
                                version_date = datetime.strptime(version['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
                                is_current = version['version_number'] == prompt['current_version']
                                
                                # Create a container for each version with better styling
                                with st.container():
                                    version_label = f"v{version['version_number']} - {version_date}"
                                    if is_current:
                                        version_label += " (current)"
                                    if st.button(version_label, 
                                               key=f"ver_{prompt['id']}_{version['version_number']}", 
                                               use_container_width=True):
                                        st.session_state['preview_version'] = version['version_number']
                        
                        with ver_col2:
                            st.markdown("#### Version Details")
                            if st.session_state['preview_version']:
                                preview_version = pm.get_prompt_version(prompt['id'], st.session_state['preview_version'])
                                if preview_version:
                                    st.markdown(f"**Title:** {preview_version['title']}")
                                    if preview_version['folder_id']:
                                        folder_name = folder_mapping.get(preview_version['folder_id'], "Unknown")
                                        st.markdown(f"*Folder: 📁 {folder_name}*")
                                    st.markdown("**Content:**")
                                    st.markdown(f"```\n{preview_version['content']}\n```")
                                    
                                    # Show resolved preview for this version
                                    with st.expander("👁️ Preview with Resolved References"):
                                        resolved_content = pm.resolve_prompt_references(preview_version['content'])
                                        st.markdown(f"```\n{resolved_content}\n```")
                                    
                                    # Only show restore button if not current version
                                    if preview_version['version_number'] != prompt['current_version']:
                                        if st.button("🔄 Restore this version", use_container_width=True):
                                            if pm.restore_version(prompt['id'], preview_version['version_number']):
                                                st.success("Version restored successfully!")
                                                st.rerun()
                            else:
                                st.info("Select a version to view details")
                        
                        st.markdown("---")
        else:
            st.info("No prompts found. Add some prompts to get started!")

# -----------------------------
# Manage Folders Section
# -----------------------------
elif choice == "Manage Folders":
    st.subheader("Manage Folders")
    # Form to add a new folder
    with st.form(key="add_folder_form"):
        new_folder_name = st.text_input("New Folder Name")
        folder_submitted = st.form_submit_button("Add Folder")
        if folder_submitted:
            if new_folder_name.strip():
                pm.add_folder(new_folder_name.strip())
                st.success("Folder added successfully!")
                st.rerun()
            else:
                st.error("Folder name cannot be empty.")

    st.markdown("---")
    folders = pm.get_folders()
    if folders:
        for folder in folders:
            with st.expander(f"📁 {folder['name']} (ID: {folder['id']})", expanded=False):
                edit_key = f"edit_folder_{folder['id']}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Edit", key=f"btn_edit_folder_{folder['id']}"):
                        st.session_state[edit_key] = not st.session_state[edit_key]
                with col2:
                    if st.button("Delete", key=f"btn_del_folder_{folder['id']}"):
                        if pm.delete_folder(folder['id']):
                            st.success("Folder deleted! Prompts in this folder are now uncategorized.")
                            st.rerun()

                if st.session_state[edit_key]:
                    with st.form(key=f"form_folder_{folder['id']}"):
                        new_name = st.text_input("Edit Folder Name", value=folder['name'])
                        submitted = st.form_submit_button("Save Changes")
                        if submitted:
                            if new_name.strip():
                                if pm.update_folder(folder['id'], new_name.strip()):
                                    st.success("Folder updated!")
                                    st.session_state[edit_key] = False
                                    st.rerun()
                            else:
                                st.error("Folder name cannot be empty.")
    else:
        st.info("No folders found. Please add a new folder above.")
