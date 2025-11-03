from flask import Blueprint
from Controllers.testimonialController import testimonial_bp

# Expose the blueprint for app registration
api_testimonial_routes = testimonial_bp


