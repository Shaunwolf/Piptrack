from app import app
import routes  # Import routes to register them
from pump_routes import pump_bp

app.register_blueprint(pump_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
