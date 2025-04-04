#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steinschliff README Generator

This script generates README.md and README_ru.md files with structured
information about ski grinding patterns from YAML configuration files.

Usage:
    ./gen_readme.py [--debug]
"""

import os
import glob
import logging
import argparse
from collections import defaultdict
from typing import Dict, List, Any, Optional, Union

# Import PyYAML library
try:
    import yaml
except ImportError:
    print("PyYAML is required for this script. Install it with pip: pip install pyyaml")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("readme_generator")

# Configuration constants
SCHLIFFS_DIR = "schliffs"
README_FILE = "README_en.md"
README_RU_FILE = "README.md"


def read_yaml_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads and parses a YAML file using PyYAML.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Dictionary with parsed YAML content or None if error occurred.

    Raises:
        Exception: If file cannot be read or parsed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


def format_snow_types(snow_types: Union[List[str], str, None]) -> str:
    """
    Formats snow type list for display in README tables.

    Args:
        snow_types: List of snow types or string.

    Returns:
        Formatted string with comma-separated snow types.
    """
    if not snow_types:
        return ""

    if isinstance(snow_types, list):
        # Filter out None values and convert to string
        valid_types = [str(item) for item in snow_types if item is not None]
        return ", ".join(valid_types)

    return str(snow_types)


def collect_structure_data() -> Dict[str, List[Dict[str, Any]]]:
    """
    Collects data from all structure YAML files.

    Returns:
        Dictionary with sections as keys and lists of structure information as values.
    """
    sections = defaultdict(list)
    yaml_files = glob.glob(f"{SCHLIFFS_DIR}/**/*.yaml", recursive=True)
    logger.info(f"Found {len(yaml_files)} YAML files")

    for file_path in yaml_files:
        data = read_yaml_file(file_path)
        if not data:
            continue

        # Determine section from directory path
        section = os.path.dirname(file_path).replace(f"{SCHLIFFS_DIR}/", "")
        if not section:
            section = "main"

        # Extract relevant information
        structure_info = {
            "name": data.get("name", os.path.basename(file_path).replace(".yaml", "")),
            "description": data.get("description", ""),
            "description_ru": data.get("description_ru", ""),
            "snow_type": format_snow_types(data.get("snow_type", [])),
            "house": data.get("house", ""),
            "country": data.get("country", ""),
            "file_path": file_path
        }

        sections[section].append(structure_info)

    return sections


def generate_english_readme(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Generates English README.md file.

    Args:
        sections: Dictionary with sections and their structure data.
    """
    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write("# Steinschliff Structures\n\n")
        f.write("This repository contains information about various ski grinding structures.\n\n")

        # Table of Contents
        f.write("## Table of Contents\n\n")
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            section_anchor = section.lower().replace(" ", "-")
            f.write(f"- [{section_title}](#{section_anchor})\n")
        f.write("\n")

        # Sections with structures
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            f.write(f"## {section_title}\n\n")

            # Table with structures
            f.write("| Name | Description | Snow Type | House | Country |\n")
            f.write("|------|------------|-----------|-------|--------|\n")

            # Sort structures by name
            structures = sorted(sections[section], key=lambda x: x["name"])

            for structure in structures:
                # Create link from name to the YAML file
                file_path = structure['file_path']
                name_with_link = f"[{structure['name']}]({file_path})"
                f.write(f"| {name_with_link} | {structure['description']} | {structure['snow_type']} | {structure['house']} | {structure['country']} |\n")

            f.write("\n")

    logger.info(f"English README.md generated successfully at {os.path.abspath(README_FILE)}")


def generate_russian_readme(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Generates Russian README_ru.md file.

    Args:
        sections: Dictionary with sections and their structure data.
    """
    with open(README_RU_FILE, 'w', encoding='utf-8') as f:
        f.write("# Структуры Steinschliff\n\n")
        f.write("Этот репозиторий содержит информацию о различных структурах для шлифовки лыж.\n\n")

        # Table of Contents
        f.write("## Оглавление\n\n")
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            section_anchor = section.lower().replace(" ", "-")
            f.write(f"- [{section_title}](#{section_anchor})\n")
        f.write("\n")

        # Sections with structures
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            f.write(f"## {section_title}\n\n")

            # Table with structures
            f.write("| Название | Описание | Тип снега | Компания | Страна |\n")
            f.write("|----------|----------|-----------|----------|--------|\n")

            # Sort structures by name
            structures = sorted(sections[section], key=lambda x: x["name"])

            for structure in structures:
                # Create link from name to the YAML file
                file_path = structure['file_path']
                name_with_link = f"[{structure['name']}]({file_path})"
                f.write(f"| {name_with_link} | {structure['description_ru']} | {structure['snow_type']} | {structure['house']} | {structure['country']} |\n")

            f.write("\n")

    logger.info(f"Russian README_ru.md generated successfully at {os.path.abspath(README_RU_FILE)}")


def main() -> None:
    """
    Main function that orchestrates the README generation process.
    """
    parser = argparse.ArgumentParser(description="Generate README files from Steinschliff structures")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    logger.info("Starting README generation")

    # Collect structure data
    sections = collect_structure_data()
    logger.info(f"Collected data for {sum(len(structures) for structures in sections.values())} structures in {len(sections)} sections")

    # Generate README files
    generate_english_readme(sections)
    generate_russian_readme(sections)

    logger.info("README generation completed successfully")


if __name__ == "__main__":
    main()