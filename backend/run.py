import os
from dotenv import load_dotenv
load_dotenv()
from app import create_app, db

app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Add models to Flask shell context"""
    from app.models import user, organization, department, asset, inventory
    return {
        'db': db,
        'User': user.User,
        'Organization': organization.Organization,
        'Department': organization.Department,
        'Asset': asset.Asset,
        'InventoryItem': inventory.InventoryItem,
        'StockMovement': inventory.StockMovement,
        'AuditLog': inventory.AuditLog,
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.environ.get('DEBUG', True))
