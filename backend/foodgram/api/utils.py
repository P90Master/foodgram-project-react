from django.http.response import HttpResponse

from recipes.models import IngredientRecipeRelation


def shopping_cart_downloader(shopping_cart_objects):
        shopping_cart = {}
        response_list = []

        # Сборка ингредиентов в словарь
        for obj in shopping_cart_objects:
            recipe = obj.recipe
            ingredients = IngredientRecipeRelation.objects.filter(
                recipe=recipe
            )

            for ingredient in ingredients:
                name = ingredient.ingredient.name
                amount = ingredient.amount
                measurement_unit = ingredient.ingredient.measurement_unit

                if name in shopping_cart.keys():
                    shopping_cart[name]['amount'] += amount

                else:
                    shopping_cart[name] = {
                        'amount': amount,
                        'measurement_unit': measurement_unit
                    }
        
        # Формирование списка
        for name in shopping_cart.keys():
            subject = shopping_cart[name]
            response_list.append(
                f'{name}: {subject["amount"]} {subject["measurement_unit"]}\n'
        )
            
        response_obj = HttpResponse(
            response_list,
            'Content-Type: text/plain'
        )
        response_obj['Content-Disposition'] = (
            'attachment;' 'filename="shopping_cart.txt"'
        )
    
        return response_obj