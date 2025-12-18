# TI-84 Plus CE - LLM Program with Alpha Lock

**How to use your TI-84 calculator as an input device for the Holy Calculator LLM**

---

## Overview

This guide shows you how to add an "LLM" program to your TI-84 Plus CE that:
1. Shows up in the PRGM menu
2. Lets you type questions using Alpha Lock
3. Sends queries to your Raspberry Pi Holy Calculator
4. Displays LLM responses on the TI-84 screen

---

## What You'll Get

When you press the **PRGM** button, you'll see:

```
┌─────────────────┐
│ EXEC EDIT NEW   │
│ 1:LLM           │ ← This is your new program!
│ 2:LLMQUICK      │ ← Quick version
│ 3:...           │
└─────────────────┘
```

---

## Two Programs Included

### 1. **LLM** - Full Featured
- Friendly interface with instructions
- Shows what you typed before sending
- Lets you ask multiple questions
- Best for first-time users

### 2. **LLMQUICK** - Fast & Minimal
- No menus, straight to typing
- One question at a time
- Best for experienced users

---

## Installation Methods

### Method 1: Manual Typing (10-15 minutes)

**Step-by-step:**

1. On your TI-84, press: **[PRGM]** → **[▶]** (right arrow to NEW) → **[ENTER]**

2. Name it: Type **LLM** then press **[ENTER]**

3. Type the program exactly as shown below

#### Program Listing: LLM

```tibasic
PROGRAM:LLM
:ClrHome
:Disp "HOLY CALCULATOR"
:Disp "LLM MODE"
:Disp "━━━━━━━━━━━━━━━━"
:Disp " "
:Disp "Alpha Lock ON"
:Disp "to type question"
:Pause

:Lbl A
:ClrHome
:Disp "━━━━━━━━━━━━━━━━"
:Disp "ENTER QUESTION:"
:Disp "━━━━━━━━━━━━━━━━"
:Disp "(Use Alpha Lock)"
:Disp " "
:Input "",Str1

:If length(Str1)=0
:Goto A

:ClrHome
:Disp "━━━━━━━━━━━━━━━━"
:Disp "SENDING TO LLM.."
:Disp "━━━━━━━━━━━━━━━━"
:Disp " "
:Disp Str1
:Disp " "
:Disp "Please wait..."
:Disp "(5-30 seconds)"

:Send({0})
:Send(Str1)
:Get(Str0)

:ClrHome
:Disp "━━━━━━━━━━━━━━━━"
:Disp "ANSWER:"
:Disp "━━━━━━━━━━━━━━━━"
:Disp " "
:Disp Str0
:Disp " "
:Pause

:ClrHome
:Menu("ASK ANOTHER?","YES",A,"NO",B)
:Lbl B
:ClrHome
:Disp "HOLY CALCULATOR"
:Disp " "
:Disp "Goodbye!"
:Stop
```

**Key Commands:**
- `ClrHome` - [PRGM] → I/O → 8:ClrHome
- `Disp` - [PRGM] → I/O → 3:Disp
- `Pause` - [PRGM] → CTL → 8:Pause
- `Lbl` - [PRGM] → CTL → 9:Lbl
- `Goto` - [PRGM] → CTL → 0:Goto
- `Input` - [PRGM] → I/O → 1:Input
- `If` - [PRGM] → CTL → 1:If
- `length(` - [2nd] [LIST] → OPS → 3:length(
- `Str1` - [VARS] → String → 1:Str1
- `Send(` - [2nd] [LINK] → B:Send(
- `Get(` - [2nd] [LINK] → A:Get(
- `Menu(` - [PRGM] → CTL → C:Menu(
- `Stop` - [PRGM] → CTL → F:Stop

### Method 2: Transfer from Computer (5 minutes)

**Using TI Connect CE:**

1. Download **TI Connect CE** from Texas Instruments website
   - Windows/Mac: https://education.ti.com/en/software/details/en/CA9C74CAD02440A69FDC7189D7E1B6C2/swticonnectcesoftware

2. Connect TI-84 to computer via USB cable

3. Convert the `.8xp.txt` files to actual `.8xp` format:
   - Use online converter: https://www.ticalc.org/
   - Or use TokenIDE: https://github.com/elfprince13/TokenIDE

4. In TI Connect CE:
   - Click "Send to Calculator"
   - Select `LLM.8xp` and `LLMQUICK.8xp`
   - Click "Send"

5. On your TI-84, press **[PRGM]** to verify programs appear

---

## How to Use

### First Time Setup

1. **Connect TI-84 to Raspberry Pi**
   - Use USB cable (TI-84 to Pi USB port)

2. **Start the interface on Raspberry Pi**
   ```bash
   cd ~/Holy-calc-pi
   source venv/bin/activate
   python3 scripts/hardware/ti84_interface.py
   ```

   You should see:
   ```
   ✓ Found TI-84 on /dev/ttyACM0
   ✓ Connected to TI-84
   TI-84 INTERFACE ACTIVE - Ready to receive queries
   ```

3. **On TI-84: Enable Alpha Lock**
   - Press **[ALPHA]** twice quickly (screen shows **A** in top-right)
   - Now typing letters is easier!

### Using the LLM Program

**Step 1: Launch**
- Press **[PRGM]**
- Select **LLM**
- Press **[ENTER]**

**Step 2: Read Instructions**
```
┌─────────────────┐
│ HOLY CALCULATOR │
│ LLM MODE        │
│ ━━━━━━━━━━━━━━━━│
│                 │
│ Alpha Lock ON   │
│ to type question│
└─────────────────┘
[Press ENTER]
```

**Step 3: Enable Alpha Lock**
- Press **[ALPHA]** twice (see **A** symbol at top)

**Step 4: Type Your Question**
```
┌─────────────────┐
│ ━━━━━━━━━━━━━━━━│
│ ENTER QUESTION: │
│ ━━━━━━━━━━━━━━━━│
│ (Use Alpha Lock)│
│                 │
│ What is 2+2?_   │
└─────────────────┘
```

**Typing Tips:**
- **Letters**: Just press the key (with Alpha Lock on)
- **Numbers**: Press [ALPHA] then the number key, OR turn off Alpha Lock temporarily
- **Spaces**: Press [ALPHA] [0]
- **Symbols**:
  - `+` = [+]
  - `-` = [-]
  - `*` = [×]
  - `/` = [÷]
  - `=` = [2nd] [MATH] (TEST menu) → 1:=
  - `?` = [ALPHA] [.]

**Step 5: Send**
- Press **[ENTER]**

**Step 6: Wait for Response**
```
┌─────────────────┐
│ ━━━━━━━━━━━━━━━━│
│ SENDING TO LLM..│
│ ━━━━━━━━━━━━━━━━│
│                 │
│ What is 2+2?    │
│                 │
│ Please wait...  │
│ (5-30 seconds)  │
└─────────────────┘
```

**Step 7: View Answer**
```
┌─────────────────┐
│ ━━━━━━━━━━━━━━━━│
│ ANSWER:         │
│ ━━━━━━━━━━━━━━━━│
│                 │
│ The answer is 4 │
│                 │
└─────────────────┘
[Press ENTER]
```

**Step 8: Ask Another?**
```
┌─────────────────┐
│ ASK ANOTHER?    │
│ 1:YES           │
│ 2:NO            │
└─────────────────┘
```

---

## Example Queries

### Math Problems

```
What is 15% of 80?
```

```
Solve for x: 2x + 5 = 13
```

```
Factor x^2 + 5x + 6
```

```
What is the derivative of x^3?
```

### Word Problems

```
If I have 10 apples and give away 3, how many do I have left?
```

```
A train goes 60 mph for 2 hours. How far does it travel?
```

### Conceptual Questions

```
Explain the quadratic formula
```

```
Why is pi irrational?
```

```
What is the Pythagorean theorem?
```

---

## Quick Version (LLMQUICK)

For experienced users who want speed:

**Step 1:** Press **[PRGM]** → **LLMQUICK** → **[ENTER]**

**Step 2:** Type question immediately (Alpha Lock ON)

**Step 3:** Press **[ENTER]**

**Step 4:** View answer

**No menus, no prompts, just type and go!**

---

## Troubleshooting

### "ERR: SYNTAX" when running program

**Fix:** Check that you typed the program correctly
- Every line starting with `:` (colon)
- Quotes around text strings `"like this"`
- Correct command names (case-sensitive)

### Program doesn't send to Pi

**Fix 1:** Make sure Pi interface is running
```bash
# On Raspberry Pi
python3 scripts/hardware/ti84_interface.py
```

**Fix 2:** Check USB connection
- Replug cable
- Try different USB port
- Check cable isn't charge-only

### No response / hangs

**Cause:** LLM queries can take 5-60 seconds
- **Wait patiently**
- Screen will update when ready
- Don't press any keys while waiting

### "ERR: UNDEFINED" for Str1 or Str0

**Fix:** Run the program once - it will create the string variables automatically

### Can't type letters

**Fix:** Enable Alpha Lock
- Press **[ALPHA]** twice quickly
- Look for **A** symbol in top-right corner

### Garbled text in response

**Fix:** Adjust baud rate on Pi side
```bash
python3 scripts/hardware/ti84_interface.py --baud 19200
```

---

## Advanced Customization

### Change Baud Rate

In the Python interface:
```bash
python3 scripts/hardware/ti84_interface.py --baud 19200
```

### Add Custom Welcome Screen

Edit line 3 in program:
```tibasic
:Disp "YOUR NAME's CALC"
```

### Save History to List

Add before `Stop`:
```tibasic
:dim(L₁)+1→dim(L₁)
:Str1→L₁(dim(L₁))
```

Now your queries save to List 1!

### Faster Send (Skip Confirmation)

Remove lines:
```tibasic
:Disp Str1
:Disp " "
:Disp "Please wait..."
```

---

## Tips for Best Experience

### Typing Speed
- **Alpha Lock** is your friend - turn it on and leave it on
- Use **[ALPHA]** + **number** for inline numbers
- Press **[CLEAR]** to fix typos

### Battery Life
- Simple math queries use SymPy (1-3 seconds, low power)
- Complex questions use LLM (10-60 seconds, more power)
- Expected runtime: 6-8 hours on Pi with 5000mAh battery

### Query Format
- **Be specific**: "Solve 2x+5=13" better than "solve equation"
- **Include context**: "What is 15% of 80?" better than "15% 80"
- **Natural language works**: "How many days in a year?" ✓

---

## File Locations

**On Mac/Dev Machine:**
- `/Users/elhoyabembe/Documents/GitHub/Holy-calc-pi/scripts/hardware/LLM.8xp.txt`
- `/Users/elhoyabembe/Documents/GitHub/Holy-calc-pi/scripts/hardware/LLMQUICK.8xp.txt`

**On Raspberry Pi:**
- Start interface: `python3 scripts/hardware/ti84_interface.py`
- Config: Edit `ti84_interface.py:30` for baud rate

**On TI-84:**
- Programs appear in **[PRGM]** menu after installation

---

## Next Steps

After you have this working:

1. **Try all types of queries** - math, word problems, explanations
2. **Customize welcome screen** with your name/style
3. **Add to startup** - Make Pi interface auto-start on boot
4. **Build enclosure** - 3D print case for Pi + TI-84 combo
5. **Add ESP32 wireless** - Go untethered with WiFi bridge

---

## Summary

**What you need:**
- TI-84 Plus CE calculator
- USB cable
- Raspberry Pi with Holy Calculator installed
- 10 minutes to type program OR 5 minutes to transfer

**What you get:**
- "LLM" button in PRGM menu
- Alpha Lock typing for questions
- Answers from Qwen2.5-Math LLM
- Works offline (no internet needed)

**How to use:**
1. Connect TI-84 to Pi via USB
2. Start Pi interface
3. Press [PRGM] → LLM → [ENTER]
4. Type question with Alpha Lock
5. Press [ENTER] and wait
6. Read answer!

---

**Ready to try it?** Connect your calculator and type your first question! 🧮✨
