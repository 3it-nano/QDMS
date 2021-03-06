from .Memristor import Memristor
import copy


class Circuit:
    """
    This class contains all the parameters for the circuit and the voltages calculation.

    Parameters
    ----------
    number_of_memristor : int
        The number of memristor that contain in the circuit.

    memristor_model : MemristorModel.Memristor.Memristor
        The memristor object which needs to inherit from Memristor class in MemristorModel.Memristor.

    gain_resistance : float
        Represents the gain of the circuit.

    v_in : float
        v_in is the voltage at the start of the circuit. (V)

    R_L : float
        Represents the resistance load (Ohm) of the wires.

    is_new_architecture : bool
        The simulator accept two types of architecture. If false, the old architecture is used, which is based on a
        voltage divider. The new architecture moves the memristor in the feedback loop of an op-amp.

    """
    def __init__(self, memristor_model, number_of_memristor, gain_resistance=0, v_in=1e-3, R_L=1,
                 is_new_architecture=True):
        if not isinstance(memristor_model, Memristor):
            print(f'Error: memristor object <{memristor_model}> doesn\'t inherited from Memristor ABC')
            exit(1)
        self.memristor_model = memristor_model
        self.number_of_memristor = number_of_memristor
        self.gain_resistance = gain_resistance
        self.v_in = v_in
        self.R_L = R_L
        self.is_new_architecture = is_new_architecture
        self.list_memristor = []
        for _ in range(number_of_memristor):
            self.list_memristor.append(copy.deepcopy(memristor_model))

    def print(self):
        print(self.memristor_model)
        print(self.number_of_memristor)
        print(self.gain_resistance)
        print(self.v_in)
        print(self.R_L)
        print(self.is_new_architecture)
        print(self.list_memristor)

    def calculate_voltage(self, conductance):
        """
        This function calculate the voltage depending on the conductance of the memristors.

        Parameters
        ----------
        conductance : float
            Conductance of the memristors (S).

        Returns
        ----------
        voltage : float
            The voltage of the circuit for this conductance.

        """
        if self.is_new_architecture:
            voltage = (1/conductance) * (self.v_in / self.R_L)
        else:
            voltage = conductance * self.gain_resistance * self.v_in
        return voltage

    def current_conductance(self):
        """
        This function return the current conductance of the circuit.
        """
        g = 0
        for res in self.list_memristor:
            g += 1 / res.read()
        return g

    def current_v_out(self):
        """
        This function return the current voltage output of the circuit.
        """
        return self.calculate_voltage(self.current_conductance())
