#!/usr/bin/env python3
"""
JARVIS — Self-Healing Bootstrap System
Auto-detects and installs missing dependencies on first run.
Makes JARVIS fully self-contained — only LLM connection is external.
"""

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


class Bootstrap:
    """Self-healing dependency manager for JARVIS."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.vendor_dir = self.project_root / "vendor"
        self.manifest_path = self.vendor_dir / "manifest.json"
        self.packages_dir = self.vendor_dir / "packages"
        self.manifest = self._load_manifest()

    # ── Public API ──

    def is_complete(self) -> bool:
        """Check if all required (core) dependencies are installed."""
        if not self.manifest:
            return False
        core = self.manifest.get("packages", {}).get("core", {})
        return all(self._check_pkg(pkg) for pkg in core.get("deps", []))

    def check_and_install(self, force: bool = False) -> bool:
        """
        Check all dependencies and install missing ones.
        Returns True if all deps are met after running.
        """
        if not self.manifest:
            print("  ⚠ No dependency manifest found — can't bootstrap.")
            return False

        missing = self._find_missing()
        if not missing and not force:
            return True

        if missing:
            print(f"\n  🔧 {len(missing)} missing dependencies detected.")
            for pkg in missing:
                print(f"     {pkg}")

        return self._auto_install(missing)

    def get_module(self, module_name: str):
        """
        Lazy-import a module with auto-install fallback.
        Usage: np = bootstrap.get_module('numpy')
        """
        try:
            return importlib.import_module(module_name)
        except ImportError:
            # Try to install just this module
            print(f"  🔧 Auto-installing '{module_name}'...")
            if self._install_package(module_name):
                return importlib.import_module(module_name)
            return None

    def check_feature(self, feature: str) -> bool:
        """Check if a specific feature tier is available."""
        if not self.manifest:
            return False
        tiers = self.manifest.get("packages", {})
        if feature not in tiers:
            return False
        return all(self._check_pkg(pkg) for pkg in tiers[feature].get("deps", []))

    def feature_status(self) -> dict:
        """Return status of all feature tiers."""
        result = {}
        if not self.manifest:
            return {"error": "No manifest"}
        for name, tier in self.manifest.get("packages", {}).items():
            deps = tier.get("deps", [])
            installed = sum(1 for pkg in deps if self._check_pkg(pkg))
            result[name] = {
                "description": tier.get("description", ""),
                "required": tier.get("required", False),
                "installed": installed == len(deps) if deps else False,
                "total": len(deps),
                "ok": installed,
            }
        return result

    def download_all(self, target_dir=None) -> bool:
        """Download all packages as wheels to vendor/packages/ for offline use."""
        if target_dir is None:
            target_dir = self.packages_dir
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Collect all unique package names from manifest
        all_pkgs = set()
        for tier in self.manifest.get("packages", {}).values():
            for dep in tier.get("deps", []):
                # Extract package name (remove version specifiers)
                name = dep.split(">=")[0].split("==")[0].split("<")[0].strip()
                all_pkgs.add(name)

        print(f"  📦 Downloading {len(all_pkgs)} packages to {target_dir}...")
        cmd = [
            sys.executable, "-m", "pip", "download",
            "--dest", str(target_dir),
        ] + list(all_pkgs)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠ Download had errors:\n{result.stderr[:500]}")
            return False

        count = len(list(target_dir.glob("*.whl"))) + len(list(target_dir.glob("*.tar.gz")))
        print(f"  ✓ Downloaded {count} packages to vendor/packages/")
        return True

    # ── Internal methods ──

    def _load_manifest(self):
        if not self.manifest_path.exists():
            return None
        try:
            with open(self.manifest_path) as f:
                return json.load(f)
        except Exception:
            return None

    def _check_pkg(self, dep_spec: str) -> bool:
        """Check if a dependency spec (e.g. 'openai>=1.0.0') is installed.
        Uses importlib.metadata to avoid actually importing (and possibly crashing on)
        packages with native extensions.
        """
        # Extract package name from pip spec
        name = dep_spec.split(">=")[0].split("==")[0].split("<")[0].strip()
        
        # Metadata names use hyphens (e.g. "edge-tts"), not underscores
        metadata_name = name.lower().replace("_", "-")
        
        # Some pip names differ from their install metadata name
        name_mapping = {
            "pillow": "Pillow",
            "pyyaml": "PyYAML",
        }
        lookup_name = name_mapping.get(metadata_name, name)
        
        try:
            from importlib import metadata as importlib_metadata
            importlib_metadata.version(lookup_name)
            return True
        except importlib_metadata.PackageNotFoundError:
            return False
        except Exception:
            # Fallback: try actual import (for edge cases)
            try:
                module_map = {
                    "edge-tts": "edge_tts",
                    "sentence-transformers": "sentence_transformers",
                }
                import_name = module_map.get(name, name.replace("-", "_"))
                importlib.import_module(import_name)
                return True
            except ImportError:
                return False

    def _find_missing(self) -> list:
        """Find all missing dependencies across all tiers."""
        missing = []
        for tier_name, tier in self.manifest.get("packages", {}).items():
            if tier.get("required", False):
                for dep in tier.get("deps", []):
                    if not self._check_pkg(dep):
                        missing.append(dep)
        return missing

    def _auto_install(self, missing: list) -> bool:
        """Automatically install missing packages via pip."""
        if not missing:
            return True

        print("\n  🔧 JARVIS is installing missing dependencies...")
        print(f"     Packages: {', '.join(m.split('>')[0].split('=')[0] for m in missing)}")

        # Prefer vendored packages but fall back to PyPI
        cmd = [sys.executable, "-m", "pip", "install"]
        if self.packages_dir.exists() and any(self.packages_dir.iterdir()):
            print("     → Using vendored packages, falling back to PyPI")
            cmd += ["--find-links", str(self.packages_dir)]
        else:
            print("     → Downloading from PyPI")
        cmd += missing

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error = result.stderr[-300:] if result.stderr else "Unknown error"
            print(f"  ⚠ Install failed: {error}")
            return False

        print("  ✓ All dependencies installed successfully!\n")
        return True

    def _install_package(self, package_name: str) -> bool:
        """Install a single package. For lazy-loading."""
        cmd = [sys.executable, "-m", "pip", "install", package_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0


# ── Singleton instance ──
_bootstrap = None


def get_bootstrap() -> Bootstrap:
    global _bootstrap
    if _bootstrap is None:
        _bootstrap = Bootstrap()
    return _bootstrap
