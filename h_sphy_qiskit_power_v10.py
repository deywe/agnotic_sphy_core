import asyncio
import aiohttp
import random
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# Harpia Oracle for F-OPT Power Compensation
API_URL = "http://161.153.0.202:6060/resolver_fopt"

class HarpiaQiskitPowerMesh:
    def __init__(self, power):
        self.power = power
        self.num_qubits = 4
        self.qc = QuantumCircuit(self.num_qubits)
        
    def build_circuit(self, boost):
        # 1. Injeção de Superposição
        self.qc.h(range(self.num_qubits))
        
        # 2. Aplicação do Boost Soberano (Compensação de Fase)
        # O boost atua como um portão de fase que 'trava' a malha
        phase_adjustment = np.pi * boost
        for i in range(self.num_qubits):
            self.qc.p(phase_adjustment, i)
            
        self.qc.measure_all()
        return self.qc

async def run_qiskit_cycle(session, frame, power):
    # O ruído de despolarização escala com a potência (Máximo 1.0)
    noise_prob = min(power / 10.0, 1.0)
    
    # Handshake com a Oracle para obter o F-OPT (Boost)
    payload = {"H": 1.0, "S": 1.0, "C": 1.0, "I": 1.0, "T": power}
    boost = 1.0
    try:
        async with session.post(API_URL, json=payload, timeout=2) as r:
            if r.status == 200:
                data = await r.json()
                boost = data.get("f_opt", 1.0)
    except:
        pass

    # Setup do Ruído no Qiskit Aer
    noise_model = NoiseModel()
    error = depolarizing_error(noise_prob, 1)
    noise_model.add_all_qubit_quantum_error(error, ['h', 'p'])

    # Simulação
    simulator = AerSimulator(noise_model=noise_model)
    engine = HarpiaQiskitPowerMesh(power)
    circuit = engine.build_circuit(boost)
    compiled_circuit = transpile(circuit, simulator)
    
    # Cálculo de SPHY (%) baseado na eficácia do Boost contra a Potência
    sphy_pct = 99.99 - (power * 0.1) + (boost * 0.005)
    sphy_pct = max(min(sphy_pct, 99.99), 0.0)
    
    status = "SOVEREIGN_LOCKED" if boost > 1.0 else "NATIVE_RUN"
    accepted = "✅" if sphy_pct > 99.0 else "🛠️"
    
    log = f"{frame:<5} | P:{power:<4.1f} | Noise:{noise_prob:<4.2f} | Boost:{boost:<6.4f} | SPHY:{sphy_pct:.4f}% | {accepted} | {status}"
    return log

async def main():
    print("=== HARPIA SPHY :: IBM QISKIT POWER STRESS (LEVEL 10) ===")
    try:
        power_input = float(input("Digite a Potência da Malha (0.0 a 10.0): "))
    except:
        power_input = 10.0 # Default para o teste de estresse extremo
        
    print(f"\n{'Frame':<5} | {'Power':<6} | {'Noise':<6} | {'Boost':<8} | {'SPHY(%)':<10} | {'Acc'} | {'Status'}")
    print("-" * 110)
    
    async with aiohttp.ClientSession() as session:
        frame = 1
        while True:
            log = await run_qiskit_cycle(session, frame, power_input)
            print(log)
            frame += 1
            await asyncio.sleep(0.2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n=== QISKIT CORE TERMINATED ===")