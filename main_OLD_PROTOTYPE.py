import serial
import numpy as np
from sympy import symbols, solve, diff, integrate, simplify, latex
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests
import asyncio
import platform

# Wolfram Alpha AppID (replace with yours)
WOLFRAM_APP_ID = "YOUR_WOLFRAM_APP_ID"

# Initialize serial for TI-84 (adjust port)
def init_ti_serial():
    try:
        return serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # TI-84 port
    except Exception as e:
        print(f"TI-84 error: {e}")
        return None

# Initialize serial for ESP32 (adjust port)
def init_esp_serial():
    try:
        return serial.Serial('/dev/ttyUSB1', 115200, timeout=1)  # ESP32 port
    except Exception as e:
        print(f"ESP32 error: {e}")
        return None

# Send/receive with TI-84
def send_to_ti84(ser, message):
    if ser:
        ser.write(message.encode() + b'\n')

def receive_from_ti84(ser):
    if ser:
        return ser.readline().decode().strip()
    return ""

# Initialize quantized LLM
def init_llm():
    model_name = "gemma_2b_quantized"  # Your saved quantized model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    return tokenizer, model

# Solve with SymPy
def solve_math_problem(expression):
    try:
        x = symbols('x')
        if "solve" in expression.lower():
            eq = expression.replace("solve", "").strip()
            solutions = solve(eq, x)
            return f"Solutions: {solutions}"
        elif "differentiate" in expression.lower():
            expr = expression.replace("differentiate", "").strip()
            derivative = diff(expr, x)
            return f"Derivative: {latex(derivative)}"
        elif "integrate" in expression.lower():
            expr = expression.replace("integrate", "").strip()
            integral = integrate(expr, x)
            return f"Integral: {latex(integral)} + C"
        else:
            result = simplify(expression)
            return f"Result: {latex(result)}"
    except Exception as e:
        return f"SymPy Error: {str(e)}"

# LLM fallback
def llm_math_fallback(tokenizer, model, query):
    inputs = tokenizer(f"Solve math: {query}", return_tensors="pt")
    outputs = model.generate(**inputs, max_length=100)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Forward to ESP32 for Wolfram API
def fetch_wolfram_via_esp(esp_ser, query):
    if esp_ser:
        esp_ser.write(f"fetch_wolfram:{query}\n".encode())
        return esp_ser.readline().decode().strip()
    return "ESP32 not connected"

async def main():
    ti_ser = init_ti_serial()
    esp_ser = init_esp_serial()
    tokenizer, model = init_llm()

    while True:
        user_input = receive_from_ti84(ti_ser)
        if user_input:
            result = solve_math_problem(user_input)
            if "Error" in result:
                result = fetch_wolfram_via_esp(esp_ser, user_input)
                if "error" in result.lower():
                    result = llm_math_fallback(tokenizer, model, user_input)
            send_to_ti84(ti_ser, result)
        await asyncio.sleep(0.1)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())





'''2. ESP32 MicroPython Script (main.py on ESP32)
Upload to ESP32 using ampy or Thonny IDE: ampy --port /dev/ttyUSB1 put main.py'''

import network
import urequests
import machine
import usys

APP_ID = "YOUR_WOLFRAM_APP_ID"  # Replace with your key

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('YOUR_SSID', 'YOUR_PASSWORD')
while not wlan.isconnected():
    pass

uart = machine.UART(0, baudrate=115200)  # For Pi communication

def fetch_wolfram(query):
    try:
        url = f"http://api.wolframalpha.com/v2/query?input={query}&appid={APP_ID}&format=plaintext"
        response = urequests.get(url)
        return response.text[:200]  # Truncate for TI-84 display
    except Exception as e:
        return f"Error: {str(e)}"

while True:
    if uart.any():
        cmd = uart.readline().decode().strip()
        if cmd.startswith("fetch_wolfram:"):
            query = cmd.split(":", 1)[1]
            result = fetch_wolfram(query)
            uart.write(result.encode() + b'\n')



