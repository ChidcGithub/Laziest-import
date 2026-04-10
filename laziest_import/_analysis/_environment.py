"""Environment detection module."""

from typing import Dict, List, Optional
import sys
import os
from dataclasses import dataclass


@dataclass
class EnvironmentInfo:
    """Information about the current Python environment."""
    python_version: str
    executable: str
    virtual_env: Optional[str]
    venv_type: Optional[str]  # 'venv', 'conda', 'virtualenv', None
    site_packages: List[str]
    installed_packages: Dict[str, str]  # package -> version


def detect_environment() -> EnvironmentInfo:
    """
    Detect the current Python environment.
    
    Returns:
        EnvironmentInfo with environment details
    """
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Executable
    executable = sys.executable
    
    # Detect virtual environment
    virtual_env = None
    venv_type = None
    
    # Check for venv/virtualenv
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        virtual_env = sys.prefix
        # Check if it's conda
        if 'conda' in sys.prefix.lower() or 'anaconda' in sys.prefix.lower():
            venv_type = 'conda'
        elif 'VIRTUAL_ENV' in os.environ:
            venv_type = 'virtualenv' if 'virtualenv' in os.environ.get('VIRTUAL_ENV', '') else 'venv'
        else:
            venv_type = 'venv'
    
    # Check for conda
    if venv_type is None and 'CONDA_PREFIX' in os.environ:
        virtual_env = os.environ['CONDA_PREFIX']
        venv_type = 'conda'
    
    # Get site-packages
    site_packages = []
    for path in sys.path:
        if 'site-packages' in path and os.path.exists(path):
            site_packages.append(path)
    
    # Get installed packages
    installed_packages = {}
    try:
        from importlib.metadata import distributions
        for dist in distributions():
            name = dist.metadata.get('Name', '')
            version = dist.metadata.get('Version', '')
            if name:
                installed_packages[name.lower()] = version
    except Exception:
        pass
    
    return EnvironmentInfo(
        python_version=python_version,
        executable=executable,
        virtual_env=virtual_env,
        venv_type=venv_type,
        site_packages=site_packages,
        installed_packages=installed_packages
    )


def show_environment() -> None:
    """Display environment information."""
    env = detect_environment()
    
    print("\n" + "=" * 60)
    print("              Environment Information")
    print("=" * 60)
    
    print(f"\nPython: {env.python_version}")
    print(f"Executable: {env.executable}")
    
    if env.virtual_env:
        print(f"Virtual Environment: {env.virtual_env}")
        print(f"Environment Type: {env.venv_type}")
    else:
        print("Virtual Environment: None (system Python)")
    
    if env.site_packages:
        print(f"\nSite Packages ({len(env.site_packages)}):")
        for sp in env.site_packages[:5]:
            print(f"  - {sp}")
        if len(env.site_packages) > 5:
            print(f"  ... and {len(env.site_packages) - 5} more")
    
    print(f"\nInstalled Packages: {len(env.installed_packages)}")
    print("=" * 60)