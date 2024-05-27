import tkinter as tk
from tkinter import font
from PIL import Image
import customtkinter
from dobot_api import *
from CTkMessagebox import CTkMessagebox
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
from cinematica_inversa import *
from cinematica_directa import *
import math

customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("blue")

current_actual = [0, 0, 0, 0, 0, 0]
feed_joint = [0.1, 0.1, 0.1, 0.1]
globalLockValue = threading.Lock()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        """Inicializa variables necesarias para la aplicación"""
        self.client_dash = None
        self.client_feed = None
        self.client_move = None
        self.global_state = {}
        self.button_list = []

        #setup_window
        self.title('Dobot MG400 - UAO -')
        self.geometry("1400x900")
        self.resizable(width=False, height=False)

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Frame connection
        self.sidebar_frame = customtkinter.CTkFrame(self, width=350, corner_radius=0, height=1000)
        self.sidebar_frame.grid(row=0, column=0, rowspan=1, sticky="nsew")
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="TCP/IP Connect",
                                                 font=customtkinter.CTkFont(family="Roboto", size=20))

        self.logo_label.place(relx=0.1, rely=0.05)

        #Entry Ip Port
        self.label_ip = customtkinter.CTkLabel(self.sidebar_frame, text="Dirección IP: ", anchor="w",
                                               font=customtkinter.CTkFont(family="Roboto", size=16))
        self.label_ip.place(relx=0.1, rely=0.15)
        self.ip_port = customtkinter.StringVar(self.sidebar_frame, value="192.168.1.6")
        self.entry_ip = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="192.168.1.6",
                                               textvariable=self.ip_port, justify="center")
        self.entry_ip.place(relx=0.5, rely=0.15)

        # Entry Dashboard Port
        self.label_dash = customtkinter.CTkLabel(self.sidebar_frame, text="Dashboard Port:", anchor="w",
                                                 font=customtkinter.CTkFont(family="Roboto", size=16))
        self.label_dash.place(relx=0.1, rely=0.20)
        self.dash_port = customtkinter.StringVar(self.sidebar_frame, value="29999")
        self.entry_dash = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="29999",
                                                 textvariable=self.dash_port, justify="center")
        self.entry_dash.place(relx=0.5, rely=0.20)

        #Entry FeedBack Port
        self.label_feed = customtkinter.CTkLabel(self.sidebar_frame, text="Feedback Port: ", anchor="w",
                                                 font=customtkinter.CTkFont(family="Roboto", size=16))
        self.label_feed.place(relx=0.1, rely=0.25)
        self.feed_port = customtkinter.StringVar(self.sidebar_frame, value="30004")
        self.entry_feed = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="30004",
                                                 textvariable=self.feed_port, justify="center")
        self.entry_feed.place(relx=0.5, rely=0.25)

        # Entry Move Port
        self.label_move = customtkinter.CTkLabel(self.sidebar_frame, text="Move Port:", anchor="w",
                                                 font=customtkinter.CTkFont(family="Roboto", size=16))
        self.label_move.place(relx=0.1, rely=0.3)
        self.move_port = customtkinter.StringVar(self.sidebar_frame, value="30003")
        self.entry_move = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="30004",
                                                 textvariable=self.move_port, justify="center")
        self.entry_move.place(relx=0.5, rely=0.3)

        #Robot Connect
        self.button_connect = customtkinter.CTkButton(self.sidebar_frame, text="Connect", width=200,
                                                      command=self.connect_port,
                                                      font=customtkinter.CTkFont(family="Roboto", size=16))
        self.button_connect.place(relx=0.33, rely=0.4)
        self.global_state["connect"] = False

        # Funciones de Dashboard
        self.dash_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.dash_frame.grid(row=1, column=0, rowspan=4, sticky="nsew")
        self.dash_frame.grid_rowconfigure(3, weight=1)
        self.dash_frame.columnconfigure(5, weight=1)

        self.button_enable = customtkinter.CTkButton(self.sidebar_frame, text="Habilitar", width=280,
                                                     fg_color="#867976",
                                                     command=self.enable, state="disabled",
                                                     font=customtkinter.CTkFont(family="Roboto", size=16))
        self.button_enable.place(relx=0.1, rely=0.5)

        self.global_state["enable"] = False

        # Entry Speed Ratio
        self.label_speed = customtkinter.CTkLabel(self.sidebar_frame, text="Speed Ratio:")
        self.label_speed.place(relx=0.1, rely=0.6)
        self.s_value = customtkinter.StringVar(self.dash_frame, value="25")
        self.entry_speed = customtkinter.CTkEntry(self.sidebar_frame, width=40, textvariable=self.s_value,
                                                  justify="center")
        self.entry_speed.place(relx=0.4, rely=0.6)
        self.label_cent = customtkinter.CTkLabel(self.sidebar_frame, text="%")
        self.label_cent.place(relx=0.55, rely=0.6)
        self.set_button = customtkinter.CTkButton(self.sidebar_frame, text="Confirm", command=self.confirm_speed,
                                                  width=70)
        self.set_button.place(relx=0.70, rely=0.6)

        # Logo Semillero
        image_tk = customtkinter.CTkImage(Image.open("files/images/LOGO-1.png"), size=(350, 260))
        my_label = customtkinter.CTkLabel(self.sidebar_frame, text="", image=image_tk)
        my_label.place(rely=0.70)

        # create tabview
        self.frame_lateral = customtkinter.CTkFrame(self, corner_radius=1)
        self.frame_lateral.grid(row=0, column=1, rowspan=4, sticky="nsew")
        self.frame_lateral.grid_columnconfigure(1, weight=1)
        self.frame_lateral.grid_rowconfigure((0, 1, 2), weight=1)
        self.frame_lateral.grid_rowconfigure(2, weight=0)

        # create tabview
        self.tabview = customtkinter.CTkTabview(self.frame_lateral, width=500, height=300)
        self.tabview.grid(row=0, column=0, padx=(10, 10), pady=(20, 15), sticky="nsew")
        self.tabview.add("C. Directa")
        self.tabview.add("C. Inversa")
        self.tabview.tab("C. Directa").grid_columnconfigure((0, 1, 2, 3), weight=1)  # configure grid of individual tabs
        self.tabview.tab("C. Inversa").grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Direct Kinematic
        labels = ["Joint 1", "Joint 2", "Joint 3", "Joint 4"]
        self.entry_list = []

        label_1 = customtkinter.CTkLabel(self.tabview.tab("C. Directa"), text=labels[0], anchor="w")
        label_1.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_directa_joint1 = customtkinter.StringVar(self.tabview.tab("C. Directa"), value="0")
        entry_1 = customtkinter.CTkEntry(self.tabview.tab("C. Directa"), placeholder_text="0",
                                         textvariable=self.cinematica_directa_joint1, justify="center")
        entry_1.grid(row=1, column=1, padx=(10, 0), pady=(5, 0), sticky="ew")
        self.entry_list.append(entry_1)

        label_2 = customtkinter.CTkLabel(self.tabview.tab("C. Directa"), text=labels[1], anchor="w")
        label_2.grid(row=0, column=2, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_directa_joint2 = customtkinter.StringVar(self.tabview.tab("C. Directa"), value="0")
        entry_2 = customtkinter.CTkEntry(self.tabview.tab("C. Directa"), placeholder_text="0",
                                         textvariable=self.cinematica_directa_joint2, justify="center")
        entry_2.grid(row=1, column=2, padx=(10, 0), pady=(5, 0), sticky="ew")
        self.entry_list.append(entry_2)

        label_3 = customtkinter.CTkLabel(self.tabview.tab("C. Directa"), text=labels[2], anchor="w")
        label_3.grid(row=2, column=1, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_directa_joint3 = customtkinter.StringVar(self.tabview.tab("C. Directa"), value="0")
        entry_3 = customtkinter.CTkEntry(self.tabview.tab("C. Directa"), placeholder_text="0",
                                         textvariable=self.cinematica_directa_joint3, justify="center")
        entry_3.grid(row=3, column=1, padx=(10, 0), pady=(5, 0), sticky="ew")
        self.entry_list.append(entry_3)

        label_4 = customtkinter.CTkLabel(self.tabview.tab("C. Directa"), text=labels[3], anchor="w")
        label_4.grid(row=2, column=2, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_directa_joint4 = customtkinter.StringVar(self.tabview.tab("C. Directa"), value="0")
        entry_4 = customtkinter.CTkEntry(self.tabview.tab("C. Directa"), placeholder_text="0",
                                         textvariable=self.cinematica_directa_joint4, justify="center")
        entry_4.grid(row=3, column=2, padx=(10, 0), pady=(5, 0), sticky="ew")
        self.entry_list.append(entry_4)

        self.button_probar_inversa = customtkinter.CTkButton(self.tabview.tab("C. Directa"), text="Probar C. Directa",
                                                             width=300, command=self.draw_dobot)
        self.button_probar_inversa.grid(row=4, column=0, columnspan=5, padx=(10, 10), pady=(30, 10))

        self.button_enviar_directa = customtkinter.CTkButton(self.tabview.tab("C. Directa"), text="Enviar", width=300,
                                                             command=self.joint_movj)
        self.button_enviar_directa.grid(row=5, column=0, columnspan=5, padx=(10, 10), pady=(10, 0))

        # Cinematica Inversa
        labels = ["Cord. X", "Cord. Y", "Cord. Z", "ROLL"]

        label_1_I = customtkinter.CTkLabel(self.tabview.tab("C. Inversa"), text=labels[0], anchor="w")
        label_1_I.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_inversa_x = customtkinter.StringVar(self.tabview.tab("C. Inversa"), value="158")
        entry_1_I = customtkinter.CTkEntry(self.tabview.tab("C. Inversa"), textvariable=self.cinematica_inversa_x,
                                           justify="center")
        entry_1_I.grid(row=1, column=1, padx=(10, 0), pady=(5, 0), sticky="ew")

        label_2_I = customtkinter.CTkLabel(self.tabview.tab("C. Inversa"), text=labels[1], anchor="w")
        label_2_I.grid(row=0, column=2, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_inversa_y = customtkinter.StringVar(self.tabview.tab("C. Inversa"), value="260")
        entry_2_I = customtkinter.CTkEntry(self.tabview.tab("C. Inversa"), textvariable=self.cinematica_inversa_y,
                                           justify="center")
        entry_2_I.grid(row=1, column=2, padx=(10, 0), pady=(5, 0), sticky="ew")

        label_3_I = customtkinter.CTkLabel(self.tabview.tab("C. Inversa"), text=labels[2], anchor="w")
        label_3_I.grid(row=2, column=1, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_inversa_z = customtkinter.StringVar(self.tabview.tab("C. Inversa"), value="-30")
        entry_3_I = customtkinter.CTkEntry(self.tabview.tab("C. Inversa"), textvariable=self.cinematica_inversa_z,
                                           justify="center")
        entry_3_I.grid(row=3, column=1, padx=(10, 0), pady=(5, 0), sticky="ew")

        label_4_I = customtkinter.CTkLabel(self.tabview.tab("C. Inversa"), text=labels[3], anchor="w")
        label_4_I.grid(row=2, column=2, padx=(10, 0), pady=(10, 0), sticky="ew")
        self.cinematica_inversa_roll = customtkinter.StringVar(self.tabview.tab("C. Inversa"), value="126")
        entry_4_I = customtkinter.CTkEntry(self.tabview.tab("C. Inversa"), textvariable=self.cinematica_inversa_roll,
                                           justify="center")
        entry_4_I.grid(row=3, column=2, padx=(10, 0), pady=(5, 0), sticky="ew")

        self.button_probar_inversa = customtkinter.CTkButton(self.tabview.tab("C. Inversa"), text="Probar C. Inversa",
                                                             width=300, command=self.draw_robot_inversa)
        self.button_probar_inversa.grid(row=4, column=0, columnspan=5, padx=(10, 10), pady=(30, 10))

        self.button_enviar_inversa = customtkinter.CTkButton(self.tabview.tab("C. Inversa"), text="Enviar", width=300,
                                                             command=self.join_movj_inversa)
        self.button_enviar_inversa.grid(row=5, column=0, columnspan=5, padx=(10, 10), pady=(10, 10))

        # Feedback
        self.frame_feed = customtkinter.CTkFrame(self.frame_lateral)
        self.frame_feed.grid(row=1, column=0, padx=(10, 10), pady=(20, 15), sticky="nsew")

        label_feedback = customtkinter.CTkLabel(self.frame_feed, text="Feedback: ")

        label_feedback.place(relx=0.1, rely=0.1)

        label1 = customtkinter.CTkLabel(self.frame_feed, text="Cord. X", anchor="w")
        label1.place(relx=0.1, rely=0.3)
        self.feed_x = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_x.place(relx=0.3, rely=0.3)

        label2 = customtkinter.CTkLabel(self.frame_feed, text="Cord. Y", anchor="w")
        label2.place(relx=0.1, rely=0.4)
        self.feed_y = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_y.place(relx=0.3, rely=0.4)

        label3 = customtkinter.CTkLabel(self.frame_feed, text="Cord. Z", anchor="w")
        label3.place(relx=0.1, rely=0.5)
        self.feed_z = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_z.place(relx=0.3, rely=0.5)

        label4 = customtkinter.CTkLabel(self.frame_feed, text="Roll", anchor="w")
        label4.place(relx=0.1, rely=0.6)
        self.feed_roll = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_roll.place(relx=0.3, rely=0.6)

        label5 = customtkinter.CTkLabel(self.frame_feed, text="Joint 1", anchor="w")
        label5.place(relx=0.6, rely=0.3)
        self.feed_j1 = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_j1.place(relx=0.8, rely=0.3)

        label6 = customtkinter.CTkLabel(self.frame_feed, text="Joint 2", anchor="w")
        label6.place(relx=0.6, rely=0.4)
        self.feed_j2 = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_j2.place(relx=0.8, rely=0.4)

        label7 = customtkinter.CTkLabel(self.frame_feed, text="Joint 3", anchor="w")
        label7.place(relx=0.6, rely=0.5)
        self.feed_j3 = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_j3.place(relx=0.8, rely=0.5)

        label8 = customtkinter.CTkLabel(self.frame_feed, text="Joint 4", anchor="w")
        label8.place(relx=0.6, rely=0.6)
        self.feed_j4 = customtkinter.CTkLabel(self.frame_feed, text="0")
        self.feed_j4.place(relx=0.8, rely=0.6)

        self.frame_matplotlib = customtkinter.CTkFrame(self.frame_lateral, border_width=1)
        self.frame_matplotlib.grid(row=0, column=1, padx=(10, 10), pady=(20, 15), sticky="nsew")

        self.canvas = tk.Canvas(self.frame_matplotlib, )
        self.canvas.pack(expand=True, fill="both")

        # Inicializa los datos tridimensionales
        X, Y = np.meshgrid(np.arange(-10, 10, 1), np.arange(-10, 10, 1))
        Z = np.zeros_like(X)

        # Crea la figura de Matplotlib
        self.fig = plt.figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlim([-500, 500])
        self.ax.set_ylim([-500, 500])
        self.ax.set_zlim([0, 500])

        # Grafica datos tridimensionales
        self.ax.plot_surface(X, Y, Z)

        # Agregar el gráfico de Matplotlib
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self.canvas)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(expand=True, fill="both")
        plt.close()

        # Document and reset robot
        self.frame_log = customtkinter.CTkFrame(self.frame_lateral)
        self.frame_log.grid(row=1, column=1, padx=(10, 10), pady=(20, 40), sticky="nsew")
        self.frame_log.grid_columnconfigure((0, 1), weight=1)
        self.frame_log.grid_rowconfigure((0, 1), weight=1)

        # Contenedor para el mensaje de advertencia
        self.container_advertencia = customtkinter.CTkFrame(self.frame_log)
        self.container_advertencia.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Texto del mensaje de advertencia
        texto_advertencia = "Al reiniciar el robot, solo se eliminan las alarmas generadas para continuar operando. Sin embargo, es crucial que investigues la causa de estas detenciones para evitar futuros problemas."

        # Crear un widget CTkLabel con el texto formateado
        self.mensaje_advertencia = customtkinter.CTkLabel(self.container_advertencia, text=texto_advertencia,
                                                          justify="left", wraplength=450)
        self.mensaje_advertencia.pack(expand=True, padx=(30, 10), pady=(20, 15), fill='both', anchor='center')

        # Contenedor para los botones
        self.container_botones = customtkinter.CTkFrame(self.frame_log)
        self.container_botones.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.button_clean = customtkinter.CTkButton(self.container_botones, text="Reiniciar Robot",
                                                    command=self.reset_clear_robot, width=150, height=45)
        self.button_clean.pack(side="left", padx=(60, 10), pady=(20, 15))

        self.button_home_robot = customtkinter.CTkButton(self.container_botones, text="Llevar Articulaciones a Home",
                                                         command=self.home_robot, width=150, height=45,
                                                         fg_color="#1EB4DD")
        self.button_home_robot.pack(side="right", padx=(0, 10), pady=(20, 15))

        # Footer
        self.frame_footer = customtkinter.CTkFrame(self.frame_lateral, height=40, bg_color="transparent",
                                                   fg_color="transparent")
        self.frame_footer.grid(row=2, column=0, columnspan=2, padx=(10, 10), pady=(20, 15), sticky="nsew")

        footer_ms = tk.Label(self.frame_footer, text="Diseñado con ❤ por el Semillero de Robótica UAO")
        emoji_font = font.Font(family="Segoe UI Emoji", size=8)  # Replace with your chosen font
        footer_ms.config(font=emoji_font)
        footer_ms.place(relx=0.6, rely=0.4)

        # Funciones

    def connect_port(self):
        if self.global_state["connect"]:
            print("Desconectado Exitosamente")
            self.client_dash.close()
            self.client_feed.close()
            self.client_move.close()
            self.client_dash = None
            self.client_feed = None
            self.client_move = None
            self.button_enable.configure(state="disabled", fg_color="#867976")  # Deshabilitar el botón

            for i in self.button_list:
                i["state"] = "disable"
            self.button_connect["text"] = "Connect"
            self.button_enable.configure(state="disabled", fg_color="#867976")  # Habilita el botón
        else:
            try:

                self.client_dash = DobotApiDashboard(
                    self.entry_ip.get(), int(self.entry_dash.get()))
                self.client_move = DobotApiMove(
                    self.entry_ip.get(), int(self.entry_move.get()))
                self.client_feed = DobotApi(
                    self.entry_ip.get(), int(self.entry_feed.get()))

            except Exception as e:

                CTkMessagebox(title="¡Advertencia!", message=f"Connection Error: {e}",
                              icon="warning", option_1="Cerrar")

                return

            for i in self.button_list:
                i["state"] = "normal"
            self.button_enable.configure(state="normal", fg_color="#22E119")  # Habilita el botón
            self.button_connect.configure(text="Disconnect", fg_color="#ED3620")
        self.global_state["connect"] = not self.global_state["connect"]
        self.set_feed_back()

    #Activar el hilo de feedback
    def set_feed_back(self):
        if self.global_state['connect']:
            thread = Thread(target=self.feed_back)
            thread.start()

    def feed_back(self):
        global current_actual
        global feed_joint
        hasRead: int = 0
        while True:
            if not self.global_state["connect"]:
                break
            data = bytes()
            while hasRead < 1440:
                temp = self.client_feed.socket_dobot.recv(1440 - hasRead)
                if len(temp) > 0:
                    hasRead += len(temp)
                    data += temp
            hasRead = 0

            feedInfo = np.frombuffer(data, dtype=MyType)
            if hex((feedInfo['test_value'][0])) == '0x123456789abcdef':
                globalLockValue.acquire()
                # Actualizar propiedades
                current_actual = feedInfo["tool_vector_actual"][0]
                feed_joint = feedInfo['q_actual'][0]
                globalLockValue.release()
                # Refrescar feedback
                self.set_feed_joint()
            time.sleep(0.005)

    def enable(self):
        if self.global_state["enable"]:
            self.client_dash.DisableRobot()
            self.button_enable.configure(text="Enable", fg_color="#867976")
        else:
            self.client_dash.EnableRobot()
            self.button_enable.configure(text="Disable", fg_color="#D32A12")

        self.global_state["enable"] = not self.global_state["enable"]

    def confirm_speed(self):
        self.client_dash.SpeedFactor(int(self.entry_speed.get()))

    #Esta función permite que el robot vuelva a habilitar su canal ante un error
    def reset_clear_robot(self):
        self.client_dash.ResetRobot()
        self.client_dash.ClearError()

    def set_feed_joint(self):
        global feed_joint
        global current_actual
        feed_joint = np.around(feed_joint, decimals=2)
        current_actual = np.around(current_actual, decimals=2)
        self.feed_x.configure(text=current_actual[0])
        self.feed_y.configure(text=current_actual[1])
        self.feed_z.configure(text=current_actual[2])
        self.feed_roll.configure(text=current_actual[3])

        self.feed_j1.configure(text=feed_joint[0])
        self.feed_j2.configure(text=feed_joint[1])
        self.feed_j3.configure(text=feed_joint[2])
        self.feed_j4.configure(text=feed_joint[3])
        #print(float(self.cinematica_directa_joint1.get()))

    def joint_movj(self):
        self.client_move.JointMovJ(float(self.cinematica_directa_joint1.get()),
                                   float(self.cinematica_directa_joint2.get()),
                                   float(self.cinematica_directa_joint3.get()),
                                   float(self.cinematica_directa_joint4.get()))

    def join_movj_inversa(self):
        valores_joint = list(range(4))
        valores_joint[0] = float(self.cinematica_inversa_x.get())
        valores_joint[1] = float(self.cinematica_inversa_y.get())
        valores_joint[2] = float(self.cinematica_inversa_z.get())
        valores_joint[3] = float(self.cinematica_inversa_roll.get())

        radians_list_feed = [math.radians(deg) for deg in feed_joint]

        q = calcular_cinematica_inversa(valores_joint, radians_list_feed[:4])

        enviar_joint_q = [math.degrees(rad) for rad in q]

        print(enviar_joint_q)
        if self.global_state['connect']:
            self.client_move.JointMovJ(float(enviar_joint_q[0]), float(enviar_joint_q[1]), float(enviar_joint_q[2]),
                                       float(enviar_joint_q[3]))
            self.client_move.Sync()

    def update_dobot_frame(self, positions):
        # Borra la visualización anterior
        self.ax.cla()

        # Actualiza las coordenadas del robot en la figura de Matplotlib
        x, y, z = zip(*positions)
        self.ax.plot(x, y, z)
        self.ax.scatter(x, y, z)

        # Se coloca una rejilla a los ejes
        self.ax.grid(True)
        # Se establecen los límites de los ejes
        self.ax.set_xlim([-500, 500])
        self.ax.set_ylim([-500, 500])
        self.ax.set_zlim([0, 500])

        # Redibuja el widget Canvas
        self.canvas_widget.draw()

    def draw_dobot(self):
        q = np.array([np.deg2rad(float(self.cinematica_directa_joint1.get())),
                      np.deg2rad(float(self.cinematica_directa_joint2.get())),
                      np.deg2rad(float(self.cinematica_directa_joint3.get())),
                      np.deg2rad(float(self.cinematica_directa_joint4.get()))])

        # Crear el manipulador
        robot = RobotManipulator(q)

        # Calcular cinemática directa
        T01, T02, T03, T04, T05 = robot.forward_kinematics()

        # Vector de posición (x, y, z) de cada sistema de coordenadas
        positions = [(0, 0, 0),
                     (T01[0, 3], T01[1, 3], T01[2, 3]),
                     (T02[0, 3], T02[1, 3], T02[2, 3]),
                     (T03[0, 3], T03[1, 3], T03[2, 3]),
                     (T04[0, 3], T04[1, 3], T04[2, 3]),
                     (T05[0, 3], T05[1, 3], T05[2, 3])]

        # Actualiza el frame de Tkinter con la representación del robot
        self.update_dobot_frame(positions)

    def draw_robot_inversa(self):
        q = np.array([np.deg2rad(float(self.cinematica_inversa_x.get())),
                      np.deg2rad(float(self.cinematica_inversa_y.get())),
                      np.deg2rad(float(self.cinematica_inversa_z.get())),
                      np.deg2rad(float(self.cinematica_inversa_roll.get()))])

        q_rad = [math.radians(deg) for deg in q]

        q = calcular_cinematica_inversa([0, 0, 0, 0], q_rad)

        joint_q = [math.degrees(rad) for rad in q]

        print(joint_q)
        # Crear el manipulador
        robot = RobotManipulator(joint_q)

        # Calcular cinemática directa
        T01, T02, T03, T04, T05 = robot.forward_kinematics()

        # Vector de posición (x, y, z) de cada sistema de coordenadas
        positions = [(0, 0, 0),
                     (T01[0, 3], T01[1, 3], T01[2, 3]),
                     (T02[0, 3], T02[1, 3], T02[2, 3]),
                     (T03[0, 3], T03[1, 3], T03[2, 3]),
                     (T04[0, 3], T04[1, 3], T04[2, 3]),
                     (T05[0, 3], T05[1, 3], T05[2, 3])]

        # Actualiza el frame de Tkinter con la representación del robot
        self.update_dobot_frame(positions)

    def home_robot(self):
        self.client_move.JointMovJ(0, 0, 0, 0)


if __name__ == "__main__":
    app = App()
    app.mainloop()
