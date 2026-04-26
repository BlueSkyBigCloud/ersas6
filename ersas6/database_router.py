class DatabaseRouter:
    """
    Routes database operations based on model type.
    """

    def db_for_read(self, model, **hints):
        """Send file storage models to MongoDB, everything else to PostgreSQL."""
        if model._meta.app_label == 'files':  # Adjust based on your file storage app name
            return 'mongodb'
        return 'default'

    def db_for_write(self, model, **hints):
        """Send file storage models to MongoDB, everything else to PostgreSQL."""
        if model._meta.app_label == 'files':
            return 'mongodb'
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Allow migrations on the right databases."""
        if app_label == 'files':
            return db == 'mongodb'
        return db == 'default'
