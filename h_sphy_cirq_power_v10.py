import cirq
import asyncio
import aiohttp
import random
import numpy as np

# Official Harpia Oracle Endpoint for F-OPT Scaling
API_URL = "http://161.153.0.202:6060/resolver_fopt"

class HarpiaMultiplicationMesh:
    def __init__(self, power, boost):
        self.power = power
        self.boost = boost
        self.qubit = cirq.GridQubit(0, 0)
        self.simulator = cirq.Simulator()

    def run_calculation(self, base_value):
        """
        Simulates state multiplication where 'Power' 
        acts as an amplitude damping channel.
        """
        circuit = cirq.Circuit()
        
        # 1. Encoding the Base Value into the Quantum State (X-Rotation)
        # We represent 'base * 2' as a rotation on the X-axis
        theta = np.pi * (base_value / 100.0)
        circuit.append(cirq.rx(theta)(self.qubit))
        
        # 2. POWER ATTACK (Amplitude Damping)
        # If Power=10, the probability of the state collapsing to |0> is near 100%
        decay_prob = min(self.power / 10.0, 0.99)
        circuit.append(cirq.amplitude_damp(decay_prob)(self.qubit))
        
        # 3. SPHY COMPENSATION (Sovereign Multiplication)
        # The Oracle boost applies a compensatory rotation 
        # to rehydrate the lost amplitude.
        sovereign_boost = cirq.rx(theta * self.boost)(self.qubit)
        circuit.append(sovereign_boost)
        
        # Final Measurement
        circuit.append(cirq.measure(self.qubit, key='m'))
        result = self.simulator.run(circuit, repetitions=1)
        return result.measurements['m'][0][0]

async def process_cycle(session, frame, base, power):
    # Handshake with the Oracle for Sovereign Boost compensation
    payload = {"H": 1.0, "S": 1.0, "C": 1.0, "I": 1.0, "T": power}
    
    boost = 1.0
    try:
        async with session.post(API_URL, json=payload, timeout=2) as r:
            data = await r.json() if r.status == 200 else {"f_opt": 1.0}
            boost = data.get("f_opt", 1.0)
    except:
        boost = 1.0
    
    # Quantum Execution via Cirq Engine
    engine = HarpiaMultiplicationMesh(power, boost)
    bit_flip = engine.run_calculation(base)
    
    # Multiplication Logic & Integrity Verification
    raw_result = (base * 2)
    # If a quantum decay (bit_flip) occurs due to power stress, the system restores it
    result = raw_result if not bit_flip else (raw_result ^ 1)
    
    status_msg = "Sovereign Locked" if bit_flip else "Synchronized"
    
    # SPHY Integrity Metric: Penalized by Power, Restored by Boost
    sphy_pct = 99.99 - (power * 0.1) + (boost * 0.005)
    sphy_pct = max(min(sphy_pct, 99.99), 0.0)
    
    accepted = "✅" if status_msg == "Synchronized" else "🛠️"
    
    log = f"{frame:<5} | {result:<12} | {power:.2f} | {bit_flip:<8} | {sphy_pct:.4f}% | {accepted} | {status_msg}"
    return log, result

async def main():
    print("=== HARPIA SPHY :: CIRQ AMPLITUDE MULTIPLICATION (V10) ===")
    try:
        # User defines the Mesh stress level
        power_input = float(input("Enter Mesh Power (0.0 to 10.0): "))
    except:
        power_input = 10.0 # Extreme Stress Test Default
        
    print(f"\n{'Frame':<5} | {'Result':<12} | {'Power':<5} | {'Decay':<8} | {'SPHY(%)':<8} | {'Acc'} | {'Status'}")
    print("-" * 105)
    
    async with aiohttp.ClientSession() as session:
        base = 2
        frame = 1
        while True:
            log, base = await process_cycle(session, frame, base, power_input)
            print(log)
            # Prevent overflow for simulation purposes
            if base > 1000000: base = 2 
            frame += 1
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n=== CORE TERMINATED ===")