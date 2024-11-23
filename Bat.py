import random
import numpy as np

class BatAlgorithm:
    def __init__(self, D, NP, N_Gen, A, r, Qmin, Qmax, Lower, Upper, function):
        self.D = D  # Dimension
        self.NP = NP  # Population size
        self.N_Gen = N_Gen  # Number of generations
        self.A = A  # Loudness
        self.r = r  # Pulse rate
        self.Qmin = Qmin  # Frequency minimum
        self.Qmax = Qmax  # Frequency maximum
        self.Lower = Lower  # Lower bound
        self.Upper = Upper  # Upper bound

        self.f_min = 0.0  # Minimum fitness
        
        self.Lb = [0] * self.D  # Lower bound for each dimension
        self.Ub = [0] * self.D  # Upper bound for each dimension
        self.Q = [0] * self.NP  # Frequency for each bat

        self.v = [[0 for _ in range(self.D)] for _ in range(self.NP)]  # Velocity
        self.Sol = [[0 for _ in range(self.D)] for _ in range(self.NP)]  # Population of solutions
        self.Fitness = [0] * self.NP  # Fitness for each bat
        self.best = [0] * self.D  # Best solution
        self.Fun = function

    def best_bat(self):
        """
        Determine the bat with the best fitness and update the global best solution.
        """
        best_index = np.argmin(self.Fitness)  # Index of the best fitness
        self.best = self.Sol[best_index][:]  # Update the best solution
        self.f_min = self.Fitness[best_index]

    def init_bat(self, model, decode_solution):
        """
        Initialize the bats' positions and velocities within the bounds.
        """
        for i in range(self.D):
            self.Lb[i] = self.Lower
            self.Ub[i] = self.Upper

        for i in range(self.NP):
            self.Q[i] = 0
            for j in range(self.D):
                rnd = np.random.uniform(0, 1)
                self.v[i][j] = 0.0
                self.Sol[i][j] = self.Lb[j] + (self.Ub[j] - self.Lb[j]) * rnd
            decoded_solution = decode_solution(self.Sol[i], model)
            if self.is_feasible(decoded_solution, model):
                self.Fitness[i] = self.Fun(self.D, self.Sol[i])
            else:
                self.Fitness[i] = float("inf")  # Penalize infeasible solutions
        self.best_bat()

    def simplebounds(self, val, lower, upper):
        """
        Ensure that the solution stays within the defined bounds.
        """
        return max(lower, min(val, upper))

    def move_bat(self, model, decode_solution):
        """
        Perform the Bat Algorithm optimization process with feasibility checks.
        """
        S = [[0.0 for _ in range(self.D)] for _ in range(self.NP)]
        self.init_bat(model, decode_solution)

        for t in range(self.N_Gen):
            for i in range(self.NP):
                rnd = np.random.uniform(0, 1)
                self.Q[i] = self.Qmin + (self.Qmax - self.Qmin) * rnd
                for j in range(self.D):
                    self.v[i][j] = self.v[i][j] + (self.Sol[i][j] - self.best[j]) * self.Q[i]
                    S[i][j] = self.Sol[i][j] + self.v[i][j]
                    S[i][j] = self.simplebounds(S[i][j], self.Lb[j], self.Ub[j])

                rnd = np.random.random_sample()
                if rnd > self.r:
                    for j in range(self.D):
                        S[i][j] = self.best[j] + 0.001 * random.gauss(0, 1)
                        S[i][j] = self.simplebounds(S[i][j], self.Lb[j], self.Ub[j])

                decoded_solution = decode_solution(S[i], model)
                if self.is_feasible(decoded_solution, model):
                    Fnew = self.Fun(self.D, S[i])
                    rnd = np.random.random_sample()
                    if (Fnew <= self.Fitness[i]) and (rnd < self.A):
                        for j in range(self.D):
                            self.Sol[i][j] = S[i][j]
                        self.Fitness[i] = Fnew

                    if Fnew <= self.f_min:
                        for j in range(self.D):
                            self.best[j] = S[i][j]
                        self.f_min = Fnew

        return self.best

    
    
def is_feasible(solution, model):
        """
        Check if a solution satisfies all hard constraints.
        """
        # Your current is_feasible implementation
        courses = model.get_courses()
        rooms = model.get_rooms()
        periods = [(d, s) for d in range(model.get_nr_days()) for s in range(model.get_nr_slots_per_day())]
        conflict_graph = model.get_conflict_graph()

        # Check lectures constraint
        lecture_assignments = {course.get_id(): 0 for course in courses}
        for course_id, room_id, day, slot in solution:
            lecture_assignments[course_id] += 1

        for course in courses:
            if lecture_assignments[course.get_id()] != course.get_nr_lectures():
                return False

        # Check conflict constraint
        for (course1, course2) in conflict_graph:
            for period in periods:
                course1_assigned = any(
                    (course1.get_id(), room.get_id(), period[0], period[1]) in solution
                    for room in rooms
                )
                course2_assigned = any(
                    (course2.get_id(), room.get_id(), period[0], period[1]) in solution
                    for room in rooms
                )
                if course1_assigned and course2_assigned:
                    return False

        # Check availability constraint
        for course_id, room_id, day, slot in solution:
            course = next(c for c in courses if c.get_id() == course_id)
            if not course.is_available(day, slot):
                return False

        # Check room occupation constraint
        room_period_assignments = {}
        for course_id, room_id, day, slot in solution:
            room_period_key = (room_id, day, slot)
            if room_period_key not in room_period_assignments:
                room_period_assignments[room_period_key] = []
            room_period_assignments[room_period_key].append(course_id)

        for assigned_courses in room_period_assignments.values():
            if len(assigned_courses) > 1:
                return False

        return True
   
