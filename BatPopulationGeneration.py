import random


class BatPopulationGeneration:
    def __init__(self, model, population_size):
        """
        Initialize the BatPopulationGeneration class.
        
        :param model: The problem model (ProblemModel).
        :param population_size: Number of bats (solutions) to generate.
        """
        self.model = model
        self.nr_days = model.nr_days
        self.nr_slots_per_day = model.nr_slots_per_day
        self.rooms = model.rooms
        self.population_size = population_size
        self.population = []

    def generate_population(self):
        """Generate a random initial population of bats (timetable solutions)."""
        for i in range(self.population_size):
            print(f"Generating Bat {i + 1}...")
            random_solution = self.create_random_solution()
            self.population.append(random_solution)
            #self.save_to_file(random_solution, f"Bat{i + 1}.out")

    def create_random_solution(self):
        """
        Create a random solution by assigning each lecture to a random room,
        and ensuring lectures of the same course have unique day and timeslot.
        """
        solution = []

        for course in self.model.courses:
            # Assign a consistent room for all lectures of this course
            room = random.choice(self.rooms)
            
            # Track used (day, slot) pairs for this course to ensure uniqueness
            used_slots = set()

            for lecture in course.lectures:
                placed = False
                while not placed:
                    day = random.randint(0, self.nr_days - 1)
                    slot = random.randint(0, self.nr_slots_per_day - 1)

                    if (day, slot) not in used_slots:
                        used_slots.add((day, slot))
                        solution.append((course.course_id, room.room_id, day, slot))
                        placed = True

        return solution

    def save_to_file(self, solution, filename):
        """
        Save a solution to a file in the required format.
        
        :param solution: The random solution for one bat.
        :param filename: Name of the file to save the solution.
        """
        with open(filename, "w") as file:
            for entry in solution:
                course_id, room_id, day, slot = entry
                file.write(f"{course_id} {room_id} {day} {slot}\n")
        print(f"Saved solution to {filename}")
