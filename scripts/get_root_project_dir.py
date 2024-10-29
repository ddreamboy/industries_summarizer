from pathlib import Path


def find_project_root(current_path: Path, marker: str = '.git') -> Path | None:
    '''
    Function to find the root directory of the project.
    
    Parameters:
    current_path (Path): The current file path.
    marker (str): The marker file or directory to identify the project root.
    
    Returns:
    Path: The root directory of the project if found, otherwise None.
    '''
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return None


def get_project_root(marker: str = '.git') -> Path:
    '''
    Get the root directory of the project.
    
    Parameters:
    marker (str): The marker file or directory to identify the project root.
    
    Returns:
    Path: The root directory of the project if found.
    
    Raises:
    FileNotFoundError: If the project root is not found.
    '''
    current_file_path = Path(__file__).resolve()
    project_root = find_project_root(current_file_path, marker)
    
    if project_root is None:
        raise FileNotFoundError('Failed to find the project root directory')
    
    return project_root


if __name__ == '__main__':
    try:
        print(get_project_root())
    except FileNotFoundError as e:
        print(e)