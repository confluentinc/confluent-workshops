import logging
from sqlalchemy.orm import Session
from app.models.models import Product, CartItem, User

logger = logging.getLogger(__name__)

class ProductService:
    """Service for product-related operations"""
    
    @staticmethod
    def get_all_products(db: Session):
        """Get all products"""
        return db.query(Product).all()
    
    @staticmethod
    def get_product_by_id(db: Session, product_id: int):
        """Get product by ID"""
        return db.query(Product).filter_by(id=product_id).first()
    
    @staticmethod
    def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int) -> bool:
        """Add product to user's cart"""
        try:
            product = db.query(Product).filter_by(id=product_id).first()
            if not product or quantity > product.quantity:
                return False
            
            # Check if product already exists in cart
            existing_cart_item = db.query(CartItem).filter_by(
                user_id=user_id, 
                product_id=product_id
            ).first()
            
            if existing_cart_item:
                # Update existing cart item quantity
                existing_cart_item.quantity += quantity
                existing_cart_item.price = product.price  # Update price in case it changed
                logger.info(f"Updated quantity for product {product_id} in cart for user {user_id}")
            else:
                # Create new cart item
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity,
                    price=product.price
                )
                db.add(cart_item)
                logger.info(f"Added new product {product_id} to cart for user {user_id}")
            
            # Update product inventory
            product.quantity -= quantity
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding product to cart: {e}")
            db.rollback()
        return False
    
    @staticmethod
    def remove_from_cart(db: Session, cart_id: int) -> bool:
        """Remove item from cart"""
        try:
            cart_item = db.query(CartItem).filter_by(id=cart_id).first()
            if cart_item:
                product = db.query(Product).filter_by(id=cart_item.product_id).first()
                if product:
                    # Find all cart items for this product and user
                    all_cart_items = db.query(CartItem).filter_by(
                        user_id=cart_item.user_id,
                        product_id=cart_item.product_id
                    ).all()
                    
                    # Calculate total quantity to restore
                    total_quantity = sum(item.quantity for item in all_cart_items)
                    
                    # Restore the total quantity to product inventory
                    product.quantity += total_quantity
                    
                    # Remove all cart items for this product
                    for item in all_cart_items:
                        db.delete(item)
                    
                    db.commit()
                    logger.info(f"Removed all instances of product {cart_item.product_id} from cart for user {cart_item.user_id}")
                    return True
        except Exception as e:
            logger.error(f"Error removing cart item {cart_id}: {e}")
            db.rollback()
        return False
    
    @staticmethod
    def get_user_cart(db: Session, user_id: int):
        """Get user's cart items consolidated by product"""
        # Get all cart items for the user
        cart_items = db.query(CartItem).filter_by(user_id=user_id).all()
        logger.info(f"Found {len(cart_items)} cart items for user {user_id}")
        
        # Consolidate items by product_id
        consolidated_cart = {}
        
        for item in cart_items:
            logger.info(f"Processing cart item: product_id={item.product_id}, quantity={item.quantity}, price={item.price}")
            if item.product_id in consolidated_cart:
                # Add quantity to existing item
                consolidated_cart[item.product_id]['quantity'] += item.quantity
                # Use the latest price (in case prices changed)
                consolidated_cart[item.product_id]['price'] = item.price
                logger.info(f"Updated existing item: product_id={item.product_id}, new_quantity={consolidated_cart[item.product_id]['quantity']}")
            else:
                # Create new consolidated item
                consolidated_cart[item.product_id] = {
                    'id': item.id,  # Keep the first cart item ID for removal
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'price': item.price,
                    'user_id': item.user_id
                }
                logger.info(f"Created new consolidated item: product_id={item.product_id}, quantity={item.quantity}")
        
        # Get product names and create final cart items
        products = {p.id: p for p in db.query(Product).all()}
        final_cart = []
        
        for product_id, cart_data in consolidated_cart.items():
            if product_id in products:
                # Create a dictionary-based cart item for better compatibility
                cart_item = {
                    'id': cart_data['id'],
                    'product_id': cart_data['product_id'],
                    'quantity': cart_data['quantity'],
                    'price': cart_data['price'],
                    'user_id': cart_data['user_id'],
                    'product_name': products[product_id].name
                }
                logger.info(f"Final cart item: product_id={cart_item['product_id']}, quantity={cart_item['quantity']}, price={cart_item['price']}, name={cart_item['product_name']}")
                final_cart.append(cart_item)
        
        logger.info(f"Returning {len(final_cart)} consolidated cart items")
        
        # Calculate total amount
        total_amount = sum(item['price'] * item['quantity'] for item in final_cart)
        logger.info(f"Cart total amount: {total_amount}")
        
        return {
            'items': final_cart,
            'total': total_amount
        } 