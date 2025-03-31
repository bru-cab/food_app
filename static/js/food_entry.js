// Food Entry Workflow Manager
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the food entry workflow
    const foodEntryWorkflow = new FoodEntryWorkflow();
    foodEntryWorkflow.init();
});

class FoodEntryWorkflow {
    constructor() {
        // Step definitions
        this.steps = [
            {
                id: 'food-info-step',
                title: 'Food Information',
                isComplete: false,
                data: {}
            },
            {
                id: 'serving-size-step',
                title: 'Serving Size',
                isComplete: false,
                data: {}
            },
            {
                id: 'nutrition-info-step', 
                title: 'Nutrition Information',
                isComplete: false,
                data: {}
            },
            {
                id: 'confirmation-step',
                title: 'Confirmation',
                isComplete: false,
                data: {}
            }
        ];
        
        this.currentStep = 0;
        this.foodData = {
            name: '',
            brand: '',
            description: '',
            quantity: 100,
            unit: 'g',
            nutrition: {},
            is_shared: false
        };
        
        // Track whether we're using manual nutrition entry
        this.isManualNutrition = false;
    }
    
    init() {
        // Set up event listeners
        document.getElementById('food-info-form').addEventListener('submit', this.handleFoodInfoSubmit.bind(this));
        document.getElementById('serving-size-form').addEventListener('submit', this.handleServingSizeSubmit.bind(this));
        document.getElementById('nutrition-form').addEventListener('submit', this.handleNutritionSubmit.bind(this));
        document.getElementById('confirmation-form').addEventListener('submit', this.handleConfirmationSubmit.bind(this));
        
        // Set up navigation buttons
        document.querySelectorAll('.step-nav-prev').forEach(button => {
            button.addEventListener('click', this.goToPreviousStep.bind(this));
        });
        
        // Set up manual nutrition toggle
        const toggleButton = document.getElementById('toggle-manual-nutrition');
        if (toggleButton) {
            toggleButton.addEventListener('click', this.toggleManualNutrition.bind(this));
        }
        
        // Initialize with the first step
        this.showStep(0);
    }
    
    // Toggle between AI and manual nutrition input
    toggleManualNutrition() {
        const manualForm = document.getElementById('manual-nutrition-form');
        const toggleButton = document.getElementById('toggle-manual-nutrition');
        const submitText = document.getElementById('nutrition-submit-text');
        
        this.isManualNutrition = !this.isManualNutrition;
        
        if (this.isManualNutrition) {
            manualForm.classList.remove('hidden');
            toggleButton.textContent = 'Use AI to calculate nutrition';
            submitText.textContent = 'Continue with Manual Values';
        } else {
            manualForm.classList.add('hidden');
            toggleButton.textContent = 'Enter nutrition values manually';
            submitText.textContent = 'Get Nutrition';
        }
    }
    
    // Set default values for manual nutrition inputs
    setDefaultManualNutritionValues() {
        // Default values
        document.getElementById('manual-calories').value = '0';
        document.getElementById('manual-energy').value = '0';
        document.getElementById('manual-protein').value = '0';
        document.getElementById('manual-carbs').value = '0';
        document.getElementById('manual-fat').value = '0';
        document.getElementById('manual-sugars').value = '0';
        document.getElementById('manual-saturated-fat').value = '0';
        document.getElementById('manual-sodium').value = '0';
        document.getElementById('manual-fiber').value = '0';
        document.getElementById('manual-fruits-veg-nuts').value = '0';
        
        // Set a default serving unit if we have it from previous steps
        if (this.steps[1] && this.steps[1].data) {
            if (this.steps[1].data.unit && document.getElementById('manual-serving-unit')) {
                document.getElementById('manual-serving-unit').value = this.steps[1].data.unit;
            }
            if (this.steps[1].data.weight && document.getElementById('manual-serving-weight')) {
                document.getElementById('manual-serving-weight').value = this.steps[1].data.weight;
            }
        }
        
        // Add listeners to update serving information when changed
        const servingUnitSelect = document.getElementById('manual-serving-unit');
        const servingWeightInput = document.getElementById('manual-serving-weight');
        
        if (servingUnitSelect && servingWeightInput) {
            servingUnitSelect.addEventListener('change', this.updateServingDescription.bind(this));
            servingWeightInput.addEventListener('input', this.updateServingDescription.bind(this));
        }
    }
    
    // Update serving description based on unit and weight
    updateServingDescription() {
        const servingUnit = document.getElementById('manual-serving-unit').value;
        const servingWeight = parseFloat(document.getElementById('manual-serving-weight').value) || 100;
        
        // Update title to show what the values are per unit
        const titleElement = document.getElementById('manual-nutrition-form').querySelector('h4');
        const servingSizeInput = document.getElementById('custom-amount') || 
                                document.getElementById('serving-size-select');
        
        const servingSize = servingSizeInput ? 
                           (servingSizeInput.value === 'custom' ? 
                            parseFloat(document.getElementById('custom-amount').value) : 
                            parseFloat(servingSizeInput.value)) : 100;
        
        if (servingUnit && servingUnit !== '') {
            titleElement.textContent = `Manual Nutrition Input (for ${servingSize}g = ${Math.round((servingSize/servingWeight) * 10) / 10} ${servingUnit}${servingSize/servingWeight !== 1 ? 's' : ''})`;
        } else {
            titleElement.textContent = `Manual Nutrition Input (for ${servingSize}g)`;
        }
        
        // Update the explanation text
        const explanationText = document.getElementById('manual-nutrition-explanation');
        if (explanationText) {
            explanationText.textContent = `Enter nutrition values for ${servingSize}g of this food, not per 100g.`;
        }
    }
    
    // Get manual nutrition values from form
    getManualNutritionValues() {
        // Get the serving unit and weight if specified
        const servingUnit = document.getElementById('manual-serving-unit') 
            ? document.getElementById('manual-serving-unit').value 
            : null;
        
        const servingWeight = document.getElementById('manual-serving-weight')
            ? parseFloat(document.getElementById('manual-serving-weight').value) || 100
            : 100;
        
        return {
            calories: parseFloat(document.getElementById('manual-calories').value) || 0,
            energy_kj: parseFloat(document.getElementById('manual-energy').value) || 0,
            protein: parseFloat(document.getElementById('manual-protein').value) || 0,
            carbs: parseFloat(document.getElementById('manual-carbs').value) || 0,
            sugars: parseFloat(document.getElementById('manual-sugars').value) || 0,
            fat: parseFloat(document.getElementById('manual-fat').value) || 0,
            saturated_fat: parseFloat(document.getElementById('manual-saturated-fat').value) || 0,
            sodium: parseFloat(document.getElementById('manual-sodium').value) || 0,
            fiber: parseFloat(document.getElementById('manual-fiber').value) || 0,
            fruits_veg_nuts: parseFloat(document.getElementById('manual-fruits-veg-nuts').value) || 0,
            unit: servingUnit,
            weight: servingWeight
        };
    }
    
    showStep(stepIndex) {
        // Hide all steps
        document.querySelectorAll('.entry-step').forEach(step => {
            step.classList.add('hidden');
        });
        
        // Show the current step
        const currentStepElement = document.getElementById(this.steps[stepIndex].id);
        currentStepElement.classList.remove('hidden');
        
        // Update progress indicator
        this.updateProgressIndicator(stepIndex);
        
        // Update the current step
        this.currentStep = stepIndex;
        
        // Initialize manual nutrition toggle if on nutrition step
        if (stepIndex === 2) {
            this.isManualNutrition = false;
            const manualForm = document.getElementById('manual-nutrition-form');
            if (manualForm) {
                manualForm.classList.add('hidden');
            }
            const toggleButton = document.getElementById('toggle-manual-nutrition');
            if (toggleButton) {
                toggleButton.textContent = 'Enter nutrition values manually';
            }
            const submitText = document.getElementById('nutrition-submit-text');
            if (submitText) {
                submitText.textContent = 'Get Nutrition';
            }
            
            // Set default values for manual inputs
            this.setDefaultManualNutritionValues();
        }
    }
    
    updateProgressIndicator(currentStepIndex) {
        const progressSteps = document.querySelectorAll('.progress-step');
        
        progressSteps.forEach((step, index) => {
            // The step is completed if it's completed explicitly or if it's before the current step and that step is marked as complete
            const isCompleted = index < currentStepIndex || this.steps[index].isComplete;
            
            if (isCompleted) {
                // Completed steps
                step.classList.add('text-white', 'bg-blue-600');
                step.classList.remove('text-gray-500', 'bg-gray-200', 'text-blue-600', 'bg-white', 'border-blue-600', 'border-2');
            } else if (index === currentStepIndex) {
                // Current step
                step.classList.remove('text-white', 'bg-blue-600', 'text-gray-500', 'bg-gray-200');
                step.classList.add('border-blue-600', 'border-2', 'text-blue-600', 'bg-white');
            } else {
                // Future steps
                step.classList.remove('text-white', 'bg-blue-600', 'border-blue-600', 'border-2', 'text-blue-600', 'bg-white');
                step.classList.add('text-gray-500', 'bg-gray-200');
            }
        });
    }
    
    goToPreviousStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }
    
    goToNextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.showStep(this.currentStep + 1);
        }
    }
    
    // Step 1: Food Information
    async handleFoodInfoSubmit(event) {
        event.preventDefault();
        
        // Get form data
        const foodName = document.getElementById('food-name').value;
        const brand = document.getElementById('food-brand').value || '';
        const description = document.getElementById('food-description').value || '';
        
        if (!foodName) {
            this.showError('food-info-error', 'Please enter a food name');
            return;
        }
        
        // Save data
        this.foodData.name = foodName;
        this.foodData.brand = brand;
        this.foodData.description = description;
        
        // Show loading state
        this.setStepLoading('food-info-step', true);
        
        try {
            // Verify food information with the API
            const response = await fetch('/api/food-info/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: foodName,
                    brand: brand,
                    description: description
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Update step data
                this.steps[0].data = data;
                this.steps[0].isComplete = true;
                
                // Update the confirmation area
                document.getElementById('confirm-food-info').textContent = data.formatted_description;
                
                // If food was found in database, show that information and store last used meal type
                if (data.found_in_db) {
                    document.getElementById('food-found-message').classList.remove('hidden');
                    const reference = data.reference;
                    const brandInfo = reference.brand && reference.brand !== 'Generic' ? ` (${reference.brand})` : '';
                    document.getElementById('food-found-message').textContent = 
                        `Found "${reference.name}${brandInfo}" in the database. Using existing nutritional information.`;
                    
                    // Store reference data for later use
                    this.foodData.reference = reference;
                    
                    // If the reference has a last used meal type, save it for later use
                    if (data.reference.last_used_meal_type) {
                        this.foodData.meal_type = data.reference.last_used_meal_type;
                    }
                } else {
                    document.getElementById('food-found-message').classList.add('hidden');
                }
                
                // Now immediately fetch the recommended serving size
                await this.fetchServingSizeData(foodName, brand, description);
                
                // Move to the next step
                this.goToNextStep();
            } else {
                this.showError('food-info-error', data.error || 'Failed to verify food information');
            }
        } catch (error) {
            console.error('Error verifying food information:', error);
            this.showError('food-info-error', 'Network error. Please try again.');
        } finally {
            this.setStepLoading('food-info-step', false);
        }
    }
    
    // Helper method to fetch serving size data
    async fetchServingSizeData(foodName, brand, description) {
        try {
            // Get recommended serving size from the API
            const response = await fetch('/api/food-info/serving-size', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: foodName,
                    brand: brand,
                    description: description
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Update step data
                this.steps[1].data = data;
                this.steps[1].isComplete = true;
                
                // Update food data with serving information
                this.foodData.quantity = data.default_serving.quantity;
                this.foodData.unit = data.unit;
                this.foodData.weight_per_unit = data.weight;
                
                // If food reference had a last used meal type, store it
                if (data.last_used_meal_type) {
                    this.foodData.meal_type = data.last_used_meal_type;
                }
                
                // Update the serving size dropdown
                const servingSizeSelect = document.getElementById('serving-size-select');
                servingSizeSelect.innerHTML = ''; // Clear existing options
                
                // Add the options
                data.options.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option.value;
                    optionElement.textContent = option.label;
                    servingSizeSelect.appendChild(optionElement);
                });
                
                // Add event listener to handle custom quantity
                servingSizeSelect.addEventListener('change', (e) => {
                    const customAmountContainer = document.getElementById('custom-amount-container');
                    if (e.target.value === 'custom') {
                        customAmountContainer.classList.remove('hidden');
                        
                        // Add input listener to the custom amount field
                        const customAmountInput = document.getElementById('custom-amount');
                        customAmountInput.addEventListener('input', this.handleCustomAmountChange.bind(this));
                        customAmountInput.focus();
                    } else {
                        customAmountContainer.classList.add('hidden');
                        this.foodData.quantity = parseFloat(e.target.value);
                        
                        // Update confirmation display with formatted serving size
                        document.getElementById('confirm-serving-size').textContent = 
                            this.formatServingSize(this.foodData.quantity, data.unit, data.weight);
                    }
                });
                
                // Set the default selection
                servingSizeSelect.value = data.default_serving.quantity;
                
                // Update the confirmation area with properly formatted serving size
                document.getElementById('confirm-serving-size').textContent = 
                    this.formatServingSize(data.default_serving.quantity, data.unit, data.weight);
                
                return data;
            } else {
                console.error('Failed to get serving size information:', data.error);
                return null;
            }
        } catch (error) {
            console.error('Error getting serving size:', error);
            return null;
        }
    }
    
    // Step 2: Serving Size
    handleCustomAmountChange() {
        const customAmountInput = document.getElementById('custom-amount');
        const customAmount = parseFloat(customAmountInput.value);
        
        if (!isNaN(customAmount) && customAmount > 0) {
            this.foodData.quantity = customAmount;
            
            // Use the saved unit and weight data to format
            if (this.steps[1].data) {
                const unit = this.steps[1].data.unit;
                const weight = this.steps[1].data.weight;
                
                // Update the confirmation display
                document.getElementById('confirm-serving-size').textContent = 
                    this.formatServingSize(customAmount, unit, weight);
            }
        }
    }
    
    async handleServingSizeSubmit(event) {
        event.preventDefault();
        
        // Show loading state
        this.setStepLoading('serving-size-step', true);
        
        try {
            // If we already have the serving size data
            if (this.steps[1].isComplete) {
                const hasReferenceData = this.steps[0].data && this.steps[0].data.found_in_db;
                
                if (hasReferenceData) {
                    // For foods from the database, get nutrition directly and skip to confirmation
                    await this.fetchNutritionFromReference();
                    // Skip to confirmation step (index 3)
                    this.goToStep(3);
                    return;
                }
                
                // Otherwise proceed normally to the nutrition step
                this.goToNextStep();
                return;
            }
            
            // Otherwise fetch the data (fallback for backward compatibility)
            await this.fetchServingSizeData(
                this.foodData.name, 
                this.foodData.brand, 
                this.foodData.description
            );
            
            // Move to the next step
            this.goToNextStep();
        } catch (error) {
            console.error('Error handling serving size submit:', error);
            this.showError('serving-size-error', 'Network error. Please try again.');
        } finally {
            this.setStepLoading('serving-size-step', false);
        }
    }
    
    // Helper method to go to a specific step
    goToStep(stepIndex) {
        if (stepIndex >= 0 && stepIndex < this.steps.length) {
            this.showStep(stepIndex);
        }
    }
    
    // Helper to fetch nutrition data from reference
    async fetchNutritionFromReference() {
        try {
            // Get nutrition information from the API
            const response = await fetch('/api/food-info/nutrition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: this.foodData.name,
                    brand: this.foodData.brand,
                    description: this.foodData.description,
                    quantity: this.foodData.quantity
                })
            });
            
            const nutritionData = await response.json();
            
            if (!response.ok) {
                throw new Error(nutritionData.error || 'Failed to get nutrition information');
            }
            
            // Update step data
            this.steps[2].data = nutritionData;
            this.steps[2].isComplete = true;
            
            // Save nutrition data
            this.foodData.nutrition = nutritionData.nutrition;
            this.foodData.adjusted_nutrition = nutritionData.adjusted_nutrition;
            this.foodData.nutri_score = nutritionData.nutri_score;
            
            // Save per serving values if they exist (for manual entries)
            if (nutritionData.per_serving) {
                this.foodData.per_serving = nutritionData.per_serving;
            }
            
            // Save reference id if available
            if (nutritionData.from_reference && nutritionData.reference_id) {
                this.foodData.reference_id = nutritionData.reference_id;
            }
            
            // Save exact serving weight if provided from the reference
            if (nutritionData.weight) {
                this.foodData.weight_per_unit = nutritionData.weight;
            }
            
            // Save serving unit if provided
            if (nutritionData.unit) {
                this.foodData.unit = nutritionData.unit;
            }
            
            // Update the confirmation area - use per_serving values for manual entry, adjusted for calculated
            const displayValues = nutritionData.per_serving && this.isManualNutrition ? 
                               nutritionData.per_serving : 
                               nutritionData.adjusted_nutrition;
                               
            document.getElementById('nutrition-calories').textContent = `${Math.round(displayValues.calories)} kcal`;
            document.getElementById('nutrition-protein').textContent = `${Math.round(displayValues.protein)}g`;
            document.getElementById('nutrition-carbs').textContent = `${Math.round(displayValues.carbs)}g`;
            document.getElementById('nutrition-fat').textContent = `${Math.round(displayValues.fat)}g`;
            
            // Display the nutri-score grade
            const nutriScoreElement = document.getElementById('nutrition-score');
            nutriScoreElement.textContent = nutritionData.nutri_score.grade;
            nutriScoreElement.className = `inline-block font-medium px-2 py-1 rounded-lg text-white ${this.getNutriScoreStyle(nutritionData.nutri_score.grade)}`;
            
            // Display source
            document.getElementById('nutrition-source').textContent = 
                this.isManualNutrition ? 'Manual entry' : nutritionData.from_reference ? 'Database' : 'AI calculation';
                
            // Update the serving size display
            const servingSize = document.getElementById('confirm-serving-size');
            
            // Display the serving size based on the unit and weight
            if (nutritionData.unit && nutritionData.unit !== 'g' && nutritionData.unit !== 'ml') {
                // Use our formatting helper with the proper weight and unit
                servingSize.textContent = this.formatServingSize(
                    this.foodData.quantity, 
                    nutritionData.unit, 
                    nutritionData.weight
                );
            } else {
                // Default to just showing grams
                servingSize.textContent = `${this.foodData.quantity}g`;
            }
            
            // Set the meal type from foodData if available
            if (this.foodData.meal_type) {
                const mealTypeSelect = document.getElementById('meal-type');
                if (mealTypeSelect && this.foodData.meal_type && mealTypeSelect.querySelector(`option[value="${this.foodData.meal_type}"]`)) {
                    mealTypeSelect.value = this.foodData.meal_type;
                }
            }
            
            return nutritionData;
        } catch (error) {
            console.error('Error fetching nutrition from reference:', error);
            throw error;
        }
    }
    
    // Step 3: Nutrition Information
    async handleNutritionSubmit(event) {
        event.preventDefault();
        
        // Get form data
        const isShared = document.getElementById('share-food-checkbox').checked;
        this.foodData.is_shared = isShared;
        
        // Get the selected serving size
        const servingSizeSelect = document.getElementById('serving-size-select');
        let quantity = parseFloat(servingSizeSelect.value);
        
        // Handle custom amount if selected
        if (servingSizeSelect.value === 'custom') {
            quantity = parseFloat(document.getElementById('custom-amount').value);
            if (!quantity || isNaN(quantity) || quantity <= 0) {
                this.showError('nutrition-error', 'Please enter a valid quantity');
                return;
            }
        }
        
        this.foodData.quantity = quantity;
        
        // Show loading state
        this.setStepLoading('nutrition-info-step', true);
        
        try {
            let nutritionData;
            
            if (this.isManualNutrition) {
                // Use manually entered values
                const manualNutrition = this.getManualNutritionValues();
                
                // Check if at least calories, protein, carbs, and fat are entered
                if (manualNutrition.calories <= 0) {
                    this.showError('nutrition-error', 'Please enter at least calories, protein, carbs, and fat values');
                    this.setStepLoading('nutrition-info-step', false);
                    return;
                }
                
                // For manual entries, if we have a unit, set the weight to the quantity
                // This ensures we show "1 slice" instead of "0.96 slices"
                if (this.steps[1] && this.steps[1].data && this.steps[1].data.unit) {
                    manualNutrition.weight = quantity;
                }
                
                // Calculate Nutri-Score from manually entered values
                const response = await fetch('/api/food-info/nutrition', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: this.foodData.name,
                        brand: this.foodData.brand,
                        description: this.foodData.description,
                        quantity: this.foodData.quantity,
                        nutrition: manualNutrition,
                        is_manual: true  // Flag to indicate manual entry
                    })
                });
                
                nutritionData = await response.json();
                
                if (!response.ok) {
                    throw new Error(nutritionData.error || 'Failed to calculate nutrition score');
                }
            } else {
                // Get nutrition information from the API
                const response = await fetch('/api/food-info/nutrition', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: this.foodData.name,
                        brand: this.foodData.brand,
                        description: this.foodData.description,
                        quantity: this.foodData.quantity
                    })
                });
                
                nutritionData = await response.json();
                
                if (!response.ok) {
                    throw new Error(nutritionData.error || 'Failed to get nutrition information');
                }
            }
            
            // Update step data
            this.steps[2].data = nutritionData;
            this.steps[2].isComplete = true;
            
            // Save nutrition data
            this.foodData.nutrition = nutritionData.nutrition;
            this.foodData.adjusted_nutrition = nutritionData.adjusted_nutrition;
            this.foodData.nutri_score = nutritionData.nutri_score;
            
            // Save per serving values if they exist (for manual entries)
            if (nutritionData.per_serving) {
                this.foodData.per_serving = nutritionData.per_serving;
            }
            
            // Save reference id if available
            if (nutritionData.from_reference && nutritionData.reference_id) {
                this.foodData.reference_id = nutritionData.reference_id;
            }
            
            // Save exact serving weight if provided from the reference
            if (nutritionData.weight) {
                this.foodData.weight_per_unit = nutritionData.weight;
            }
            
            // Save serving unit if provided
            if (nutritionData.unit) {
                this.foodData.unit = nutritionData.unit;
            }
            
            // Update the confirmation area - use per_serving values for manual entry, adjusted for calculated
            const displayValues = nutritionData.per_serving && this.isManualNutrition ? 
                               nutritionData.per_serving : 
                               nutritionData.adjusted_nutrition;
                               
            document.getElementById('nutrition-calories').textContent = `${Math.round(displayValues.calories)} kcal`;
            document.getElementById('nutrition-protein').textContent = `${Math.round(displayValues.protein)}g`;
            document.getElementById('nutrition-carbs').textContent = `${Math.round(displayValues.carbs)}g`;
            document.getElementById('nutrition-fat').textContent = `${Math.round(displayValues.fat)}g`;
            
            // Display the nutri-score grade
            const nutriScoreElement = document.getElementById('nutrition-score');
            nutriScoreElement.textContent = nutritionData.nutri_score.grade;
            nutriScoreElement.className = `inline-block font-medium px-2 py-1 rounded-lg text-white ${this.getNutriScoreStyle(nutritionData.nutri_score.grade)}`;
            
            // Display source
            document.getElementById('nutrition-source').textContent = 
                this.isManualNutrition ? 'Manual entry' : nutritionData.from_reference ? 'Database' : 'AI calculation';
            
            // Update the serving size display
            const servingSize = document.getElementById('confirm-serving-size');
            
            // Display the serving size based on the unit and weight
            if (nutritionData.unit && nutritionData.unit !== 'g' && nutritionData.unit !== 'ml') {
                // Use our formatting helper with the proper weight and unit
                servingSize.textContent = this.formatServingSize(
                    this.foodData.quantity, 
                    nutritionData.unit, 
                    nutritionData.weight
                );
            } else {
                // Default to just showing grams
                servingSize.textContent = `${this.foodData.quantity}g`;
            }
            
            // Set the meal type from foodData if available
            if (this.foodData.meal_type) {
                const mealTypeSelect = document.getElementById('meal-type');
                if (mealTypeSelect && this.foodData.meal_type && mealTypeSelect.querySelector(`option[value="${this.foodData.meal_type}"]`)) {
                    mealTypeSelect.value = this.foodData.meal_type;
                }
            }
            
            // Move to the next step
            this.goToNextStep();
        } catch (error) {
            console.error('Error getting nutrition info:', error);
            this.showError('nutrition-error', error.message || 'Network error. Please try again.');
        } finally {
            this.setStepLoading('nutrition-info-step', false);
        }
    }
    
    // Step 4: Confirmation and Save
    async handleConfirmationSubmit(event) {
        event.preventDefault();
        
        // Get meal type
        const mealTypeSelect = document.getElementById('meal-type');
        this.foodData.meal_type = mealTypeSelect.value;
        
        // Get sharing preference
        this.foodData.is_shared = document.getElementById('share-food-checkbox').checked;
        
        // Combine all data for saving
        const finalData = {
            name: this.foodData.name,
            brand: this.foodData.brand,
            description: this.foodData.description,
            quantity: this.foodData.quantity,
            meal_type: this.foodData.meal_type,
            is_shared: this.foodData.is_shared,
            nutrition: this.foodData.nutrition
        };
        
        // If we have a reference ID, include it to avoid creating duplicates
        if (this.foodData.reference_id) {
            finalData.reference_id = this.foodData.reference_id;
        }
        
        // Show loading state
        this.setStepLoading('confirmation-step', true);
        
        try {
            // Save food entry
            const response = await fetch('/api/food', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(finalData)
            });
            
            if (response.ok) {
                // Show success message
                this.showSuccess('confirmation-success', 'Food entry saved successfully!');
                
                // Reset the form and workflow after a delay
                setTimeout(() => {
                    this.resetWorkflow();
                    location.reload(); // Reload to update the food entries list
                }, 1500);
            } else {
                this.showError('confirmation-error', data.error || 'Failed to save food entry');
            }
        } catch (error) {
            console.error('Error saving food entry:', error);
            this.showError('confirmation-error', 'Network error. Please try again.');
        } finally {
            this.setStepLoading('confirmation-step', false);
        }
    }
    
    // Utility methods
    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorElement.classList.add('hidden');
        }, 5000);
    }
    
    showSuccess(elementId, message) {
        const successElement = document.getElementById(elementId);
        successElement.textContent = message;
        successElement.classList.remove('hidden');
        
        // Hide after 5 seconds
        setTimeout(() => {
            successElement.classList.add('hidden');
        }, 5000);
    }
    
    setStepLoading(stepId, isLoading) {
        const stepElement = document.getElementById(stepId);
        const submitButton = stepElement.querySelector('button[type="submit"]');
        const loadingIndicator = stepElement.querySelector('.loading-indicator');
        
        if (isLoading) {
            submitButton.disabled = true;
            loadingIndicator.classList.remove('hidden');
        } else {
            submitButton.disabled = false;
            loadingIndicator.classList.add('hidden');
        }
    }
    
    resetWorkflow() {
        // Reset all form inputs
        document.getElementById('food-info-form').reset();
        document.getElementById('serving-size-form').reset();
        document.getElementById('nutrition-form').reset();
        document.getElementById('confirmation-form').reset();
        
        // Reset workflow state
        this.currentStep = 0;
        this.steps.forEach(step => {
            step.isComplete = false;
            step.data = {};
        });
        
        // Reset food data
        this.foodData = {
            name: '',
            brand: '',
            description: '',
            quantity: 100,
            unit: 'g',
            nutrition: {},
            is_shared: false
        };
        
        // Show the first step
        this.showStep(0);
    }
    
    // Helper function to get Nutri-Score style
    getNutriScoreStyle(grade) {
        const styles = {
            'A': 'bg-[#038141]',  // Very Good (Dark Green)
            'B': 'bg-[#85BB2F]',  // Good (Light Green)
            'C': 'bg-[#FECB02]',  // Moderate (Yellow)
            'D': 'bg-[#EE8100]',  // Poor (Orange)
            'E': 'bg-[#E63E11]'   // Bad (Red)
        };
        return styles[grade] || 'bg-gray-500';
    }
    
    // Helper function to format serving size display
    formatServingSize(quantity, unit, weight) {
        // Ensure valid inputs with defaults
        quantity = parseFloat(quantity) || 100;
        weight = parseFloat(weight) || quantity;
        unit = unit || 'g';
        
        // Check if quantity is exactly the same as weight (custom weight per unit)
        const isExactMatch = Math.abs(quantity - weight) < 0.01;
        // If quantity is close to weight (within 5%), just show it as one unit
        const isCloseToWeight = Math.abs(quantity - weight) / weight < 0.05;
        
        if (unit === 'g' || unit === 'ml') {
            return `${quantity}${unit}`;
        } else if (isExactMatch && (unit === 'slice' || unit === 'piece' || unit === 'cookie' || unit === 'egg')) {
            // For a custom defined unit where quantity is exactly weight
            return `${quantity}g (1 ${unit})`;
        } else if (isCloseToWeight && (unit === 'slice' || unit === 'piece')) {
            // For a single slice or piece when weight is close to quantity
            return `${quantity}g (1 ${unit})`;
        } else if (unit === 'cookie') {
            const numCookies = Math.round((quantity / weight) * 10) / 10;
            return `${quantity}g (${numCookies} ${numCookies === 1 ? 'cookie' : 'cookies'})`;
        } else if (unit === 'piece' || unit === 'slice' || unit === 'unit') {
            const numPieces = Math.round((quantity / weight) * 10) / 10;
            return `${quantity}g (${numPieces} ${numPieces === 1 ? unit : unit + 's'})`;
        } else if (unit === 'egg') {
            const numEggs = Math.round((quantity / weight) * 10) / 10;
            return `${quantity}g (${numEggs} ${numEggs === 1 ? 'egg' : 'eggs'})`;
        } else if (unit === 'cup' || unit === 'tbsp' || unit === 'tsp') {
            // Handle volume-based measurements
            const numUnits = Math.round((quantity / weight) * 10) / 10;
            const unitNames = {
                'cup': 'cup',
                'tbsp': 'tablespoon',
                'tsp': 'teaspoon'
            };
            const unitName = unitNames[unit] || unit;
            return `${quantity}g (${numUnits} ${unitName}${numUnits === 1 ? '' : 's'})`;
        } else if (unit) {
            // For any other custom unit
            return `${quantity}g (${unit})`;
        } else {
            return `${quantity}g`;
        }
    }
} 