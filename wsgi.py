from alter_igo import create_app
import socket


hostname = socket.gethostname()
hostaddr = socket.gethostbyname(hostname)
app = create_app()

if __name__ == '__main__':
    app.run(host=hostaddr, port=5000, debug=False)