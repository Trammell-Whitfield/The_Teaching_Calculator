# TI-84 Quick Start Guide

Get your TI-84 Plus CE connected to the Holy Calculator in **15 minutes**.

---

## Prerequisites

- TI-84 Plus CE calculator
- USB cable (TI-84 to Raspberry Pi)
- Raspberry Pi 5 with Holy Calculator installed
- **Optional**: TI Connect CE software (for loading programs)

---

## NEW: Alpha Lock LLM Interface

**Want the easiest way to use your TI-84 with the Holy Calculator?**

See **[TI84_LLM_ALPHA_LOCK_GUIDE.md](TI84_LLM_ALPHA_LOCK_GUIDE.md)** for:
- "LLM" program that appears in your PRGM menu
- Type questions using Alpha Lock (no special codes!)
- Simple press-and-go interface

**This is the recommended method for most users!**

---

## Step 1: Install Dependencies (2 minutes)

On your Raspberry Pi:

```bash
# Activate virtual environment
cd ~/Holy_Calculator
source venv/bin/activate

# Install serial communication library
pip install pyserial

# Test connection
python3 scripts/hardware/ti84_interface.py --test
```

You should see:
```
✓ Calculator engine ready
TEST MODE: Simulating TI-84 queries
📩 Test query: Solve: 2x + 5 = 13
✓ Solved by sympy in 0.02s
```

---

## Step 2: Connect TI-84 via USB (1 minute)

1. Plug USB cable into TI-84
2. Plug other end into Raspberry Pi USB port
3. On Pi, check connection:

```bash
# List USB devices
lsusb | grep -i "texas"

# Should show something like:
# Bus 001 Device 005: ID 0451:e003 Texas Instruments, Inc. ...
```

4. Find serial port:

```bash
ls /dev/tty* | grep -E "ttyACM|ttyUSB"

# Should show:
# /dev/ttyACM0  (most common for TI-84)
```

---

## Step 3: Load Program to TI-84 (5 minutes)

### Option A: Type it manually (fastest)

On your TI-84:

1. Press `[PRGM]` → `[NEW]` → `[1:Create New]`
2. Name it: `HOLYSIMPL`
3. Type this program:

```tibasic
:ClrHome
:Disp "HOLY CALCULATOR"
:Lbl A
:Input "QUERY:",Str1
:Send({Str1})
:Get(Str0)
:Disp "RESULT:"
:Disp Str0
:Pause
:Disp "AGAIN? (1=Y)"
:Input A
:If A=1:Goto A
```

4. Press `[2nd]` `[MODE]` (QUIT) to save

### Option B: Use TI Connect CE (more features)

1. Download TI Connect CE: https://education.ti.com/en/products/computer-software/ti-connect-ce-sw
2. Connect TI-84 to your computer via USB
3. Open TI Connect CE
4. Copy `scripts/hardware/HOLYCALC.8xp.txt` to TI-84
5. Disconnect and move TI-84 to Pi

---

## Step 4: Start Holy Calculator Interface (1 minute)

On Raspberry Pi:

```bash
# Run TI-84 interface
python3 scripts/hardware/ti84_interface.py

# You should see:
# ✓ Found TI-84 on /dev/ttyACM0
# ✓ Connected to TI-84 on /dev/ttyACM0
# ✓ Calculator engine ready
# ====================================
# TI-84 INTERFACE ACTIVE
# ====================================
# Press Ctrl+C to stop
```

**Leave this running!** This is the server that listens for TI-84 queries.

---

## Step 5: Test It! (1 minute)

On your TI-84:

1. Press `[PRGM]`
2. Select `HOLYSIMPL`
3. Press `[ENTER]` to run
4. At the `QUERY:` prompt, type: `"2+2"`
5. Press `[ENTER]`

**On the Pi terminal**, you should see:
```
📩 Received: 2+2
✓ Solved by sympy in 0.01s
📤 Answer: 4.0
```

**On the TI-84 screen**, you should see:
```
RESULT:
4.0
```

**Success!** 🎉

---

## Usage Examples

Try these queries on your TI-84:

### Basic Math
```
QUERY: 123 + 456
→ 579.0

QUERY: 2^10
→ 1024.0
```

### Algebra
```
QUERY: Solve: 2x + 5 = 13
→ x = 4

QUERY: Factor: x^2 + 5x + 6
→ (x + 2)*(x + 3)
```

### Calculus
```
QUERY: Derivative of x^2 + 3x
→ 2x + 3

QUERY: Integrate: x^2
→ x^3/3 + C
```

### Word Problems (slower - uses LLM)
```
QUERY: If I have 10 apples and eat 3, how many are left?
→ 7 apples remain
(Wait 10-30 seconds)
```

---

## Troubleshooting

### "No TI-84 detected"
**Fix:**
```bash
# Check USB connection
lsusb | grep -i texas

# Try specifying port manually
python3 scripts/hardware/ti84_interface.py --port /dev/ttyACM0
```

### "Permission denied" on /dev/ttyACM0
**Fix:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Reboot
sudo reboot
```

### TI-84 shows "ERR:SYNTAX"
**Fix:**
- Make sure you typed the program exactly as shown
- Check for missing colons (`:`) at start of lines
- Variables are case-sensitive: use `Str1`, not `str1`

### No response on TI-84
**Fix:**
1. Check Pi interface is running (see Step 4)
2. Verify USB cable is connected
3. Try different USB port on Pi
4. Restart TI-84: `[2nd]` `[+]` (MEM) → `[7:Reset]` → `[1:All RAM]`

### Garbled text on TI-84
**Fix:**
```bash
# Try different baud rate
python3 scripts/hardware/ti84_interface.py --baud 19200
```

---

## Next Steps

### 1. Add More Query Types
Modify `HOLYSIMPL` to include templates:

```tibasic
:Menu("SELECT:","SOLVE",1,"DIFF",2,"CUSTOM",3)
:Lbl 1
:Input "EQN:",Str2
:"Solve: "+Str2→Str1
:Goto S
:Lbl 2
:Input "F(X):",Str2
:"Derivative of "+Str2→Str1
:Goto S
:Lbl 3
:Input "QUERY:",Str1
:Lbl S
:Send({Str1})
:Get(Str0)
:Disp Str0
```

### 2. Enable Wolfram Alpha
```bash
# Create .env file with API key
echo "WOLFRAM_ALPHA_APP_ID=your_key" > .env

# Run with Wolfram enabled
python3 scripts/hardware/ti84_interface.py --enable-wolfram
```

### 3. Auto-Start on Boot
```bash
# Create systemd service
sudo nano /etc/systemd/system/holy-calc-ti84.service
```

```ini
[Unit]
Description=Holy Calculator TI-84 Interface
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Holy_Calculator
ExecStart=/home/pi/Holy_Calculator/venv/bin/python3 \
    /home/pi/Holy_Calculator/scripts/hardware/ti84_interface.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable holy-calc-ti84
sudo systemctl start holy-calc-ti84

# Check status
sudo systemctl status holy-calc-ti84
```

### 4. Wireless Option (ESP32)
See `docs/ESP32_SETUP.md` for wireless bridge setup (coming soon!)

---

## Tips & Tricks

### Speed Up Responses
- **SymPy queries** (algebra, calculus) are instant (<1s)
- **LLM queries** (word problems, proofs) take 10-60s
- Use SymPy whenever possible for speed

### Battery Life
- TI-84 uses minimal power (<50mA)
- Pi 5 + calculator system: 6-8 hours on 5000mAh battery
- Disable Wolfram Alpha for longer runtime (saves WiFi power)

### History Feature
Add to your program:

```tibasic
:dim(L₁)+1→dim(L₁)
:Str1→L₁(dim(L₁))  // Save query to list L₁
```

View history:
```tibasic
:For(I,1,dim(L₁))
:Disp L₁(I)
:End
```

### Screen Formatting
Results >16 chars will wrap. For better display:

```tibasic
:Get(Str0)
:For(I,1,length(Str0),16)
:Disp sub(Str0,I,16)
:End
```

---

## Advanced: Full Menu System

See `scripts/hardware/HOLYCALC.8xp.txt` for complete program with:
- Menu-driven interface
- Query templates
- History tracking
- Error handling
- Multiple display modes

Transfer using TI Connect CE for full experience.

---

## Reference Card

Print and tape to TI-84:

```
┌─────────────────────────────────┐
│  HOLY CALCULATOR QUICK REF      │
├─────────────────────────────────┤
│ RUN: [PRGM] → HOLYSIMPL → ENTER │
│                                 │
│ QUERY TYPES:                    │
│   2+2                           │
│   Solve: x^2 = 4                │
│   Factor: x^2+5x+6              │
│   Derivative of x^3             │
│   Integrate: x^2                │
│                                 │
│ SYMBOLS:                        │
│   ^ = [^]    x = [X,T,θ,n]     │
│   = = [2nd][TEST][1]            │
└─────────────────────────────────┘
```

---

**You're ready to go!** Enjoy your portable math-solving powerhouse. 🧮🥧
