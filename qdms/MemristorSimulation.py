import itertools
import math
import time
import numpy as np
from .Circuit import Circuit
from .Data_Driven import Data_Driven


def spread_resistor_list(lrs, hrs, nb_states, number):
    """
    This function help the create_res_states() function

    Parameters
    ----------
    number : int
        The number of distribution to create

    lrs : float
        Low Resistance State (LRS) (Ohm)

    hrs : float
         High Resistance State (HRS) (Ohm)

    nb_states : int
        The number of states used to program the memristor.

    Returns
    ----------
    list_resistor : iterable[float]
        list of resistor (Ohm)

    """
    list_resistor = []
    for j in range(number):
        # This equation can be optimized. It create a number of different resistance values.
        temp = [int(lrs + i * ((hrs -
                lrs) / (nb_states - 1)) +
                ((-1) ** j) * ((j + 1) // 2) * ((hrs - lrs)
                / ((nb_states - 1) * 4 * 2))) for i in range(nb_states)]
        temp[0] = lrs
        temp[-1] = hrs
        list_resistor.append(temp)
    return list_resistor


class MemristorSimulation:
    """
    This class contains all the parameters for the memristor simulation.
    After initializing the parameters values, start the simulation with self.simulate()

    Parameters
    ----------
    circuit : Circuit.Circuit
        The circuit object.

    nb_states : int
        The number of states wanted.

    list_resistance : iterable[iterable[float]]
        Contains the targets resistance (Ohm).

    distribution_type : string
        The distribution type can add controlled variability to the voltages output by targeting individual resistance
        values for the memristor's states. A plot of the distribution is output in Resist folder. The possibilities are:
            'linear' : The states are chosen in a linear manner.
            'full_spread' : All the memristor have a different distribution.

    is_using_conductance : bool
        If true, the distribution of the resistance used will be found with conductance instead of resistance. Linear
        distribution will therefore be non-linear.

    verbose : bool
        If true, the simulation will output parameter description and timer on how much time left to the simulation.

    voltages_memristor : dict
        Dictionary where the key is the voltage output and the package is the resistance value of each memristor

    timers : list of float
        Contains the different timers of the simulation. (s)

    start_loop_rec, start_inner_loop_rec, self.end_loop_rec, end_inner_loop_rec : float
        Different timers used in the recursive loop (s)
    """
    def __init__(self, circuit, nb_states, distribution_type='linear', is_using_conductance=False, verbose=False):
        if not isinstance(circuit, Circuit):
            raise TypeError(f'Error: circuit object is not from Circuit class.')
        # if distribution_type != 'full_spread' and distribution_type != 'linear':
        #     raise Exception(f"Error: distribution type <{distribution_type}> invalid")
        self.circuit = circuit
        self.nb_states = nb_states
        self.distribution_type = distribution_type
        self.list_resistance = self.create_res_states()
        self.is_using_conductance = is_using_conductance
        self.voltages_memristor = {}
        self.verbose = verbose

        # Inner parameters
        self.timers = []  # [List_resist, loop_rec, sorting_cutting, creating_plots, total]
        self.start_loop_rec = 0
        self.start_inner_loop_rec = 0
        self.end_loop_rec = 0
        self.end_inner_loop_rec = 0

    def presentation(self):
        """
        This function print the main parameters of the memristor simulation.
        """
        print("-------------------------")
        print('New architecture:\t' + str(self.circuit.is_new_architecture))
        print('Number of memristor:\t' + str(self.circuit.number_of_memristor))
        print(f'Number of states:\t{self.nb_states}')
        if isinstance(self.circuit.memristor_model, Data_Driven):
            print(f'Memristor model:\t{type(self.circuit.memristor_model)}\t{self.circuit.memristor_model.parameter_model}')
        else:
            print(f'Memristor model:\t{type(self.circuit.memristor_model)}')
        print(f'Distribution type:\t{self.distribution_type}')
        print("-------------------------")

    def print(self):
        print(self.nb_states)
        print(self.distribution_type)
        print(self.list_resistance)
        print(self.is_using_conductance)
        print(len(self.voltages_memristor))
        print(self.verbose)

    def simulate(self):
        """
        Function to simulate all the possible voltages of the circuit and is stored in self.voltages.
        """
        if self.verbose:
            self.presentation()

        if self.distribution_type == 'linear':
            self.simulate_linear()
        elif self.distribution_type == 'full_spread':
            self.simulate_loop()

        self.voltages_memristor = {k: self.voltages_memristor[k] for k in sorted(self.voltages_memristor)}

        for i in self.circuit.list_memristor:
            i.g = 1 / i.r_on

        return self.voltages_memristor

    def simulate_linear(self):
        if self.verbose:
            timer_start = time.time()
        res_values = list(itertools.combinations_with_replacement(self.list_resistance[0], self.circuit.number_of_memristor))
        counter = 0
        if self.verbose:
            timer_start_ = time.time()
        for current_res in res_values:
            if counter % 500000 == 0 and self.verbose:
                print(f'Done: {counter}\tLeft: {len(res_values) - counter}')
                took = round(time.time() - timer_start_, 2)
                print(f'Total time elapsed: {time.time() - timer_start}s\tTime Left: {took * (len(res_values) - counter) / 500000}')
                timer_start_ = time.time()

            for i in range(self.circuit.number_of_memristor):
                self.circuit.list_memristor[i].g = 1 / current_res[i]
            self.voltages_memristor[round(self.circuit.current_v_out(), 12)] = current_res
            counter += 1
        if self.verbose:
            print(f'Total time: {round(time.time() - timer_start, 2)}s')
            print()

    def simulate_loop(self):
        current_states = []
        for _ in range(self.circuit.number_of_memristor):
            current_states.append(-1)

        if self.verbose:
            timer_start = time.time()
            self.start_loop_rec = time.time()
        self.loop_rec(self.list_resistance, self.circuit.number_of_memristor, current_states)
        if self.verbose:
            timer_end = time.time()
            self.timers.append(timer_end-timer_start)
            print()

    def create_res_states(self):
        """
        This function creates the theoretical resistance distribution according to the distribution_type.

        Returns
        ----------
        res_states : list of list of float
            list of resistor (Ohm)
        """
        lrs = self.circuit.memristor_model.r_on
        hrs = self.circuit.memristor_model.r_off
        res_states = []
        if self.distribution_type == 'linear':
            res_states = [[int(lrs + i * ((hrs - lrs) / (self.nb_states - 1))) for i in range(self.nb_states)]]
        elif self.distribution_type == 'full_spread':
            res_states = spread_resistor_list(lrs, hrs, self.nb_states, self.circuit.number_of_memristor)
        return res_states

    def add_voltage(self, list_resistance, current_states):
        """
        This function calculate the resistance or conductance depending on the simulation parameters
        and calculate one output voltage of the circuit.

        Parameters
        ----------
        list_resistance : iterable[float][float]
            The list of all resistances (Ohm)

        current_states : list of int
            Contains the states of all loops from the recursive loop.

        Returns
        ----------

        """
        current_res = []
        j = 0
        for i in current_states:
            current_res.append(list_resistance[j][i])
            j += 1

        for i in range(self.circuit.number_of_memristor):
            self.circuit.list_memristor[i].g = 1 / current_res[i]
        self.voltages_memristor[round(self.circuit.current_v_out(), 12)] = [1/i.g for i in self.circuit.list_memristor]

    def loop_rec(self, list_resistance, counter, current_states):
        """
        This function is a recursive loop which calls a number of loops equal to the amount of memristor in the circuit.

        Parameters
        ----------
        list_resistance : list of float
            The list of all resistances (Ohm)

        counter : int
            Keep count of the number of iteration

        current_states : iterable[int]
            Contains the states of all loops from the recursive loop.
        """
        if counter == self.circuit.number_of_memristor - 1 and self.verbose:
            self.end_loop_rec = time.time()
            self.end_inner_loop_rec = time.time()
            print(f'Total time elapsed: {round(self.end_loop_rec - self.start_loop_rec, 2)}s; '
                  f'Loop time: {round(self.end_inner_loop_rec - self.start_inner_loop_rec, 2)}s')
            loop_remaining = self.nb_states - current_states[counter]
            print(f'Loops remaining: {loop_remaining}; Expected remaining time: '
                  f'{round(loop_remaining * (self.end_inner_loop_rec - self.start_inner_loop_rec), 2)}s')
            self.start_inner_loop_rec = time.time()
        if counter >= 1:
            for x in range(self.nb_states):
                current_states[counter-1] = x
                self.loop_rec(list_resistance, counter - 1, current_states)
        else:
            self.add_voltage(list_resistance, current_states)
