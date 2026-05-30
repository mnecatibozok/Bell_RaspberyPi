# 🔔 School Bell System

> 🇹🇷 [Türkçe açıklama için tıklayın → README.tr.md](README.tr.md)

A browser-based school bell management system that runs on a Raspberry Pi. Schedule bells, play sounds, manage music, monitor presence with a camera — all from a web interface you can open on any phone or computer on your school network.

---

## What Does It Do?

- **Rings bells automatically** at the times you schedule
- **Plays MP3 music** between lessons (with a built-in music player)
- **Detects presence** using a USB camera and AI (YOLOv8) — can trigger bells when someone enters a room
- **Announces** pre-recorded audio clips (earthquake alert, national anthem, student announcements, etc.)
- **Controls a relay** to physically switch an amplifier or bell on and off
- **Accessible from any device** on the school network via a web browser — no app to install

---

## What You Need

| Item | Details |
|---|---|
| Raspberry Pi | Model 4B or 5 recommended (2 GB RAM minimum) |
| MicroSD card | 16 GB or larger, Class 10 |
| Power supply | Official Raspberry Pi power adapter |
| USB speaker or amplifier | Anything with a 3.5 mm or USB audio input |
| USB camera (optional) | For presence detection |
| Relay module (optional) | To physically control a bell or amplifier |
| A monitor (first setup only) | You can go headless afterwards |

---

## Step-by-Step Setup

### Step 1 — Install Raspberry Pi OS

> **Think of this like installing Windows on a new computer.**

1. On another computer, download **Raspberry Pi Imager** from: https://www.raspberrypi.com/software/
2. Insert your microSD card into a card reader on that computer.
3. Open Raspberry Pi Imager.
4. Click **"Choose OS"** → select **"Raspberry Pi OS (64-bit)"** (the one with a desktop).
5. Click **"Choose Storage"** → select your microSD card.
6. Click the **gear icon** (⚙️) to open advanced settings:
   - Set a **hostname** (e.g. `bellpi`)
   - Set a **username** and **password** (write these down!)
   - Enable **SSH** (so you can connect remotely later)
   - Enter your **Wi-Fi name and password** if using Wi-Fi
7. Click **"Write"** and wait for it to finish (~5 minutes).
8. Put the microSD card into the Raspberry Pi, plug in the power, and wait ~2 minutes for it to boot.

---

### Step 2 — Connect to the Pi and Update It

> **You only need to do this once.**

Connect a monitor and keyboard to the Pi (or SSH into it). Then open a **Terminal** and run:

```bash
sudo apt update && sudo apt upgrade -y
```

This updates all the system software. It may take 5–10 minutes. Grab a coffee. ☕

Then install Python 3 (usually already installed):

```bash
sudo apt install python3 python3-pip -y
```

---

### Step 3 — Copy the Bell System Files to the Pi

1. Download the **zil-v1-kamera-fix20.zip** file from the Releases section of this page.
2. Copy it to the Pi. The easiest way:
   - Plug a USB stick into your regular computer, copy the ZIP there, then plug the USB stick into the Pi.
   - Or use a file manager to drag the file to the Pi over the network.
3. On the Pi, open the **File Manager**, navigate to the Desktop, and create a new folder called `zil`.
4. Move the ZIP file into that folder, right-click it, and select **"Extract Here"**.

Your folder should now look like this:

```
/home/abc/Desktop/zil/
    zil-programi-v1.html
    bell-start.sh
    INSTALLATION.txt
    zunucu/
        sunucu.py
        ...
    zilsesleri/
        zil.mp3
        siren.mp3
        ...
```

> ⚠️ **Important:** The username `abc` in the paths above is an example. Replace it with the username you chose in Step 1 (e.g. `pi`, `admin`, or whatever you set).

---

### Step 4 — (Optional) Install the AI Camera Feature

> Skip this step if you don't have a USB camera or don't need presence detection.

Open a Terminal and run:

```bash
cd /home/abc/Desktop/zil
bash zunucu/ai_kur.sh
```

This downloads the YOLOv8-nano AI model (~6 MB) and installs its dependencies. It may take 10–15 minutes on a slow connection.

---

### Step 5 — Start the System

**Option A — Double-click (easiest):**

Double-click the file called `Zil-Baslat.desktop` on the Desktop.
If it asks "Do you want to run this?", click **"Run"**.

**Option B — Terminal:**

```bash
bash /home/abc/Desktop/zil/bell-start.sh
```

A browser window will open automatically showing the Bell System interface.

---

### Step 6 — Open the Interface From Another Device

Once the system is running, you can control it from **any phone, tablet, or computer** on the same Wi-Fi network.

1. Find the Pi's IP address: open a Terminal on the Pi and type:
   ```bash
   hostname -I
   ```
   You'll see something like `192.168.1.42`.

2. On your phone or another computer, open a browser and go to:
   ```
   http://192.168.1.42:8765/zil-programi-v1.html
   ```
   (Replace `192.168.1.42` with your Pi's actual IP address.)

---

### Step 7 — (Optional) Start Automatically on Boot

Want the bell system to start by itself every time the Pi turns on?

Open a Terminal and run these two commands:

```bash
mkdir -p /home/abc/.config/autostart
cp /home/abc/Desktop/zil/zil-autostart.desktop /home/abc/.config/autostart/zil.desktop
```

Now whenever the Pi boots, the Bell System starts automatically. No keyboard needed.

---

## Adding Your Own Bell Sounds

Put your `.mp3` sound files into the `zilsesleri/` folder inside the `zil` folder. The system will detect them automatically on the next start.

> Supported format: **MP3**. Filename can be anything, but avoid spaces — use underscores instead (e.g. `school_bell.mp3`).

---

## Adding Background Music

Create a folder called `mp3` inside the `zil` folder, then create sub-folders for each playlist:

```
zil/
  mp3/
    morning/
      song1.mp3
      song2.mp3
    break/
      song3.mp3
```

The system will scan these folders and make them available in the Music Player panel.

---

## Stopping the System

To stop the server, open a Terminal and run:

```bash
pkill -f sunucu.py
```

To also close the browser:

```bash
pkill chromium
```

---

## Troubleshooting

**The browser doesn't open automatically**
→ Open Chromium manually and go to `http://localhost:8765/zil-programi-v1.html`

**No sound plays**
→ Check that the speaker is connected and the Pi's audio output is set to the correct device. Run `alsamixer` in the Terminal and make sure the volume is not muted.

**The camera feed doesn't appear**
→ Make sure the USB camera is plugged in before starting the server. Check with `ls /dev/video*` — you should see `/dev/video0`.

**The system doesn't start automatically on boot**
→ Check that the path in `zil-autostart.desktop` matches your actual username and folder location.

**I changed the Pi's username — paths are broken**
→ Open `zil-baslat.sh`, `bell-start.sh`, and `zil-autostart.desktop` in a text editor and replace `abc` with your actual username.

---

## Language

The interface has a **TR / EN** language toggle in the top-right corner. Click it to switch between Turkish and English at any time.

---

## License

This project is developed for educational use. Feel free to adapt it for your school.
