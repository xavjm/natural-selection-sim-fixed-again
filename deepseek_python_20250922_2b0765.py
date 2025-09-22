import numpy as np
import pygame
import random
import math
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Simulation parameters
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (240, 240, 240)
FPS = 60

# Genetic traits
NUM_TRAITS = 3  # Speed, size, camouflage
TRAIT_NAMES = ["Speed", "Size", "Camouflage"]

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Natural Selection Simulation")
clock = pygame.time.Clock()

class Entity:
    def __init__(self, x, y, traits=None, is_predator=False):
        self.x = x
        self.y = y
        self.energy = 100
        self.age = 0
        self.max_age = random.randint(500, 1000)
        self.is_predator = is_predator
        
        if traits is None:
            self.traits = {
                "Speed": random.uniform(0.5, 2.0),
                "Size": random.uniform(0.5, 2.0),
                "Camouflage": random.uniform(0.0, 1.0)
            }
        else:
            self.traits = traits
            
        # Mutate slightly
        for trait in self.traits:
            if random.random() < 0.2:  # 20% mutation chance
                self.traits[trait] += random.uniform(-0.2, 0.2)
                self.traits[trait] = max(0.1, min(2.0, self.traits[trait]))
                
        # Size affects energy costs and visibility
        self.radius = int(5 * self.traits["Size"])
        
        # Speed affects movement but increases energy consumption
        self.speed = 2 * self.traits["Speed"]
        
        # Camouflage affects detection range
        self.camouflage = self.traits["Camouflage"]
        
        # Color based on traits (RGB)
        r = int(255 * (1 - self.camouflage) if is_predator else int(150 * self.camouflage))
        g = int(100 * self.traits["Speed"])
        b = int(150 * self.traits["Size"])
        self.color = (r, g, b) if is_predator else (r, g, b)
        
    def move(self, target_x, target_y):
        # Calculate direction
        dx = target_x - self.x
        dy = target_y - self.y
        dist = max(0.1, math.sqrt(dx*dx + dy*dy))
        
        # Normalize and apply speed
        dx /= dist
        dy /= dist
        
        # Move
        self.x += dx * self.speed
        self.y += dy * self.speed
        
        # Keep within bounds
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        
        # Energy cost based on speed and size
        self.energy -= 0.05 * self.speed * self.traits["Size"]
        
    def draw(self, surface):
        # Draw the entity
        pygame.gfxdraw.filled_circle(
            surface, 
            int(self.x), 
            int(self.y), 
            self.radius, 
            self.color
        )
        
        # Draw a border for predators
        if self.is_predator:
            pygame.gfxdraw.aacircle(
                surface,
                int(self.x),
                int(self.y),
                self.radius,
                (255, 0, 0)
            )
            
    def can_see(self, other, is_predator_view=False):
        # Calculate distance
        dx = other.x - self.x
        dy = other.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Detection range based on size and camouflage
        detection_range = 150 * (1 if is_predator_view else self.traits["Size"])
        detection_range *= (1 - other.camouflage) if not other.is_predator else 1
        
        return dist < detection_range
        
    def reproduce(self):
        # Reproduction cost
        if self.energy > 150 and random.random() < 0.01:
            self.energy -= 50
            
            # Create offspring with similar traits
            child_traits = {}
            for trait, value in self.traits.items():
                child_traits[trait] = value + random.uniform(-0.1, 0.1)
                child_traits[trait] = max(0.1, min(2.0, child_traits[trait]))
                
            return Entity(
                self.x + random.uniform(-20, 20),
                self.y + random.uniform(-20, 20),
                child_traits,
                self.is_predator
            )
        return None

class Food:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.energy = 20
        self.radius = 3
        
    def draw(self, surface):
        pygame.gfxdraw.filled_circle(
            surface,
            int(self.x),
            int(self.y),
            self.radius,
            (0, 200, 0)
        )

class Simulation:
    def __init__(self):
        self.preys = [Entity(random.uniform(0, WIDTH), random.uniform(0, HEIGHT)) for _ in range(20)]
        self.predators = [Entity(random.uniform(0, WIDTH), random.uniform(0, HEIGHT), is_predator=True) for _ in range(5)]
        self.foods = [Food() for _ in range(30)]
        self.generation = 0
        self.max_preys = 0
        self.max_predators = 0
        
    def update(self):
        # Age entities and remove dead ones
        for entity in self.preys + self.predators:
            entity.age += 1
            entity.energy -= 0.1
            
        # Remove dead preys
        self.preys = [prey for prey in self.preys if prey.energy > 0 and prey.age < prey.max_age]
        
        # Remove dead predators
        self.predators = [pred for pred in self.predators if pred.energy > 0 and pred.age < pred.max_age]
        
        # Add new food occasionally
        if random.random() < 0.05 or len(self.foods) < 10:
            self.foods.append(Food())
            
        # Prey behavior
        for prey in self.preys:
            # Find nearest food
            nearest_food = None
            min_dist = float('inf')
            for food in self.foods:
                dx = food.x - prey.x
                dy = food.y - prey.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < min_dist:
                    min_dist = dist
                    nearest_food = food
                    
            # Find nearest predator
            nearest_predator = None
            min_pred_dist = float('inf')
            for predator in self.predators:
                if predator.can_see(prey, is_predator_view=True):
                    dx = predator.x - prey.x
                    dy = predator.y - prey.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < min_pred_dist:
                        min_pred_dist = dist
                        nearest_predator = predator
            
            # Move away from predators or toward food
            if nearest_predator and min_pred_dist < 100:
                # Flee from predator
                prey.move(2*prey.x - nearest_predator.x, 2*prey.y - nearest_predator.y)
            elif nearest_food:
                # Move toward food
                prey.move(nearest_food.x, nearest_food.y)
                
                # Eat food if close enough
                dx = nearest_food.x - prey.x
                dy = nearest_food.y - prey.y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < prey.radius + nearest_food.radius:
                    prey.energy += nearest_food.energy
                    self.foods.remove(nearest_food)
            else:
                # Random movement
                prey.move(
                    prey.x + random.uniform(-50, 50),
                    prey.y + random.uniform(-50, 50)
                )
                
            # Reproduction
            offspring = prey.reproduce()
            if offspring:
                self.preys.append(offspring)
                
        # Predator behavior
        for predator in self.predators:
            # Find nearest prey
            nearest_prey = None
            min_dist = float('inf')
            for prey in self.preys:
                if predator.can_see(prey, is_predator_view=True):
                    dx = prey.x - predator.x
                    dy = prey.y - predator.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_prey = prey
            
            # Hunt prey or move randomly
            if nearest_prey:
                predator.move(nearest_prey.x, nearest_prey.y)
                
                # Catch prey if close enough
                dx = nearest_prey.x - predator.x
                dy = nearest_prey.y - predator.y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < predator.radius + nearest_prey.radius:
                    predator.energy += 30
                    if nearest_prey in self.preys:
                        self.preys.remove(nearest_prey)
            else:
                # Random movement
                predator.move(
                    predator.x + random.uniform(-50, 50),
                    predator.y + random.uniform(-50, 50)
                )
                
            # Reproduction
            offspring = predator.reproduce()
            if offspring:
                self.predators.append(offspring)
                
        # Update statistics
        self.max_preys = max(self.max_preys, len(self.preys))
        self.max_predators = max(self.max_predators, len(self.predators))
        
        # If population is too low, add new entities
        if len(self.preys) < 5:
            self.preys.append(Entity(random.uniform(0, WIDTH), random.uniform(0, HEIGHT)))
            
        if len(self.predators) < 2:
            self.predators.append(Entity(random.uniform(0, WIDTH), random.uniform(0, HEIGHT), is_predator=True))
            
        self.generation += 1
        
    def draw(self, surface):
        # Draw background
        surface.fill(BACKGROUND_COLOR)
        
        # Draw food
        for food in self.foods:
            food.draw(surface)
            
        # Draw preys
        for prey in self.preys:
            prey.draw(surface)
            
        # Draw predators
        for predator in self.predators:
            predator.draw(surface)
            
        # Draw stats
        font = pygame.font.SysFont(None, 24)
        stats_text = [
            f"Preys: {len(self.preys)}",
            f"Predators: {len(self.predators)}",
            f"Generation: {self.generation}",
            f"Max Preys: {self.max_preys}",
            f"Max Predators: {self.max_predators}"
        ]
        
        for i, text in enumerate(stats_text):
            text_surface = font.render(text, True, (0, 0, 0))
            surface.blit(text_surface, (10, 10 + i * 25))
            
        # Draw trait averages if there are preys
        if self.preys:
            avg_traits = {trait: 0 for trait in TRAIT_NAMES}
            for prey in self.preys:
                for trait in TRAIT_NAMES:
                    avg_traits[trait] += prey.traits[trait]
                    
            for trait in TRAIT_NAMES:
                avg_traits[trait] /= len(self.preys)
                
            trait_text = [
                f"Avg {trait}: {avg_traits[trait]:.2f}" for trait in TRAIT_NAMES
            ]
            
            for i, text in enumerate(trait_text):
                text_surface = font.render(text, True, (0, 0, 0))
                surface.blit(text_surface, (WIDTH - 200, 10 + i * 25))

# Create simulation
simulation = Simulation()

# Main game loop
running = True
paused = False

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_r:
                # Reset simulation
                simulation = Simulation()
                
    # Update simulation if not paused
    if not paused:
        simulation.update()
        
    # Draw everything
    simulation.draw(screen)
    
    # Display pause message if paused
    if paused:
        font = pygame.font.SysFont(None, 48)
        text = font.render("PAUSED", True, (255, 0, 0))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        
    # Update display
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(FPS)

pygame.quit()