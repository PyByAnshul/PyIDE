from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import pty
import select
import threading
import uuid
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/')
def editor():
    return render_template('index.html')

socketio = SocketIO(app, cors_allowed_origins="*")

fd = None

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    
@socketio.on('run')
def handle_run(data):
    global fd
    code = data.get('code', '')
    run_id = data.get('run_id', '')
    if not code:
        emit('output', {'output': '[Error] No code received.\n', 'run_id': run_id})
        return

    file_id = str(uuid.uuid4())
    file_path = f"{file_id}.py"
    with open(file_path, "w") as code_file:
        code_file.write(code)

    def execute_code():
        global fd
        try:
            pid, fd = pty.fork()
            if pid == 0:
                os.execvp("python3", ["python3", file_path])
            else:
                output_buffer = ""
                while True:
                    r, _, _ = select.select([fd], [], [], 0.1)
                    if r:
                        try:
                            output = os.read(fd, 1024).decode()
                            output_buffer += output
                            socketio.emit('output', {'output': output, 'run_id': run_id})
                        except OSError:
                            break

                    pid_done, status = os.waitpid(pid, os.WNOHANG)
                    if pid_done != 0:
                        break


                if os.WIFEXITED(status):
                    exit_code = os.WEXITSTATUS(status)
                    if exit_code == 0 and "Traceback" not in output_buffer:
                        socketio.emit('output', {'output': "\n✅ Code ran successfully.\n", 'run_id': run_id})
                    else:
                        socketio.emit('output', {'output': f"\n❌ Code exited with errors (code {exit_code}).\n", 'run_id': run_id})
                else:
                    socketio.emit('output', {'output': "\n❌ Process terminated abnormally.\n", 'run_id': run_id})
        except Exception as e:
            traceback.print_exc()
            socketio.emit('output', {'output': f"\n[Exception] {str(e)}", 'run_id': run_id})
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            fd = None

    thread = threading.Thread(target=execute_code)
    thread.start()

@socketio.on('input')
def handle_input(data):
    global fd
    user_input = data.get('input', '')
    if fd is not None:
        try:
            os.write(fd, user_input.encode())
        except Exception as e:
            emit('output', f"\n[Error] Failed to send input: {str(e)}")
    else:
        emit('output', "[Error] No active session to send input.")


if __name__ == '__main__':
    app.run(debug=True)