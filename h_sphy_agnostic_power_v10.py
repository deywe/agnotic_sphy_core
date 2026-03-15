import asyncio
import aiohttp
import random
import time

# Official Oracle Endpoint for F-OPT Resolution
API_URL = "http://161.153.0.202:6060/resolver_fopt"

async def process_cycle(session, frame, base, power):
    # Bit-Flip is now a direct function of Input Power
    # Power > 0.8 triggers the "stress" in the quantum mesh
    threshold = 0.3 * power 
    bit_flip = 1 if random.random() < threshold else 0
    
    # State Processing
    raw_result = (base * 2) ^ bit_flip
    # If a bit-flip occurs, the system attempts to restore integrity
    result = raw_result ^ bit_flip if bit_flip else raw_result
    status_msg = "Failure Corrected" if bit_flip else "Synchronized"

    # Communication with the Oracle for Boost Compensation
    payload = {
        "H": random.uniform(0.95, 1.0), 
        "S": random.uniform(0.95, 1.0), 
        "C": random.uniform(0.95, 1.0), 
        "I": random.uniform(0.95, 1.0), 
        "T": power
    }
    
    try:
        async with session.post(API_URL, json=payload, timeout=2) as r:
            data = await r.json() if r.status == 200 else {"f_opt": 1.0}
            boost = data.get("f_opt", 1.0)
    except:
        boost = 1.0
    
    # SPHY(%) penalizes Power, but the Sovereign Boost restores integrity
    sphy_pct = 99.99 - (power * 0.1) + (boost * 0.005)
    sphy_pct = max(min(sphy_pct, 99.99), 0.0)
    
    accepted = "✅" if status_msg == "Synchronized" else "🛠️"
    
    log = f"{frame:<5} | {result:<12} | {power:.2f} | {bit_flip:<8} | {sphy_pct:.4f}% | {accepted} | {status_msg}"
    return log, result

async def main():
    print("=== HARPIA SPHY :: DYNAMIC POWER MODULE ===")
    try:
        # Scaling up: controlling the Operational Power of the Mesh
        power_input = float(input("Enter Mesh Power (0.0 to 10.0): "))
    except:
        power_input = 1.0
        
    print(f"\n{'Frame':<5} | {'Result':<12} | {'Power':<5} | {'Bit-Flip':<8} | {'SPHY(%)':<8} | {'Acc'} | {'Status'}")
    print("-" * 100)
    
    async with aiohttp.ClientSession() as session:
        base = 2
        frame = 1
        while True:
            log, base = await process_cycle(session, frame, base, power_input)
            print(log)
            frame += 1
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n=== CORE TERMINATED ===")
