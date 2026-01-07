"""
Board file I/O operations (.wboard format)
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path

from whiteboard.storage.database import Database
from whiteboard.objects import NoteObject, TextObject, ImageObject


class BoardFile:
    """
    Handles .wboard file format (ZIP with SQLite + assets)
    """

    def __init__(self, file_path=None):
        """
        Initialize board file

        Args:
            file_path: Path to .wboard file
        """
        self.file_path = file_path
        self.temp_dir = None

    def save(self, objects, file_path=None):
        """
        Save objects to .wboard file

        Args:
            objects: List of canvas objects to save
            file_path: Path to save file (overrides constructor path)
        """
        if file_path:
            self.file_path = file_path

        if not self.file_path:
            raise ValueError("No file path specified")

        # Create temporary directory for building archive
        self.temp_dir = tempfile.mkdtemp(prefix='whiteboard_')

        try:
            # Create database in temp directory
            db_path = os.path.join(self.temp_dir, 'board.db')
            db = Database(db_path)
            db.connect()
            db.create_schema()
            db.save_objects(objects)
            db.close()

            # Create assets directory
            assets_dir = os.path.join(self.temp_dir, 'assets')
            os.makedirs(assets_dir, exist_ok=True)

            # Copy image assets
            image_map = {}
            for obj in objects:
                if isinstance(obj, ImageObject) and obj.image_path:
                    # Generate asset filename
                    original_path = obj.image_path
                    if original_path not in image_map:
                        # Use object ID as filename to ensure uniqueness
                        ext = Path(original_path).suffix
                        asset_name = f"{obj.id}{ext}"
                        asset_path = os.path.join(assets_dir, asset_name)

                        # Copy image file
                        if os.path.exists(original_path):
                            shutil.copy2(original_path, asset_path)
                            image_map[original_path] = asset_name

            # Update database with asset paths
            if image_map:
                db = Database(db_path)
                db.connect()

                for obj in objects:
                    if isinstance(obj, ImageObject) and obj.image_path:
                        if obj.image_path in image_map:
                            # Update the data field with relative asset path
                            import json
                            obj_dict = obj.to_dict()
                            data = json.loads(obj_dict['data'])
                            data['asset_path'] = f"assets/{image_map[obj.image_path]}"

                            cursor = db.conn.cursor()
                            cursor.execute('''
                                UPDATE objects
                                SET data = ?
                                WHERE id = ?
                            ''', (json.dumps(data), obj.id))

                db.conn.commit()
                db.close()

            # Create ZIP archive
            with zipfile.ZipFile(self.file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add database
                zf.write(db_path, 'board.db')

                # Add assets
                if os.path.exists(assets_dir) and os.listdir(assets_dir):
                    for asset_file in os.listdir(assets_dir):
                        asset_path = os.path.join(assets_dir, asset_file)
                        zf.write(asset_path, f'assets/{asset_file}')

        finally:
            # Clean up temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None

    def load(self, file_path=None):
        """
        Load objects from .wboard file

        Args:
            file_path: Path to load file (overrides constructor path)

        Returns:
            List of canvas objects
        """
        if file_path:
            self.file_path = file_path

        if not self.file_path:
            raise ValueError("No file path specified")

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        # Create temporary directory for extraction
        self.temp_dir = tempfile.mkdtemp(prefix='whiteboard_')

        try:
            # Extract ZIP archive
            with zipfile.ZipFile(self.file_path, 'r') as zf:
                zf.extractall(self.temp_dir)

            # Load database
            db_path = os.path.join(self.temp_dir, 'board.db')
            if not os.path.exists(db_path):
                raise ValueError("Invalid .wboard file: missing board.db")

            db = Database(db_path)
            db.connect()
            obj_dicts = db.load_objects()
            db.close()

            # Create objects from dictionaries
            objects = []
            for obj_dict in obj_dicts:
                obj_type = obj_dict['type']

                # Handle asset paths
                if obj_type == 'image':
                    import json
                    data = json.loads(obj_dict['data'])
                    asset_path = data.get('asset_path', '')

                    # Convert to absolute path in temp directory
                    if asset_path and not os.path.isabs(asset_path):
                        data['asset_path'] = os.path.join(self.temp_dir, asset_path)
                        obj_dict['data'] = json.dumps(data)

                # Create object based on type
                if obj_type == 'note':
                    obj = NoteObject.from_dict(obj_dict)
                elif obj_type == 'text':
                    obj = TextObject.from_dict(obj_dict)
                elif obj_type == 'image':
                    obj = ImageObject.from_dict(obj_dict)
                else:
                    continue  # Skip unknown types

                objects.append(obj)

            return objects

        except Exception as e:
            # Clean up on error
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            raise e

    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
