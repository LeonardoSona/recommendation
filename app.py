import streamlit as st
import pandas as pd
import json
import ast
from datetime import datetime
import os

# Set page config
st.set_page_config(
    page_title="Product Recommendation System",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []

def load_data(uploaded_file=None):
    """Load recommendation data from uploaded file or create sample data"""
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            return df
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return None
    else:
        # Create sample data based on your example for demonstration
        sample_data = {
            'MUDID': ['ai730048'],
            'Recommended_Product': [str([152415, 101115, 222273, 100161, 222453, 100349, 209207])],
            'Final_Score': [str([0.8, 0.11, 0.11, 0.11, 0.11, 0.11, 0.11])],
            'RF_Score': [str([0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35])],
            'CF_Score': [str([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])],
            'Visited_Studies': [str(['152415'])],
            'SHAP': [str([{152415: [{'feature': 'user_ACCOUNT_ACTIVE_Y', 'value': 0.0, 'impact': 0.05}]}])]
        }
        df = pd.DataFrame(sample_data)
        return df

def parse_list_string(list_str):
    """Safely parse string representation of list"""
    try:
        return ast.literal_eval(list_str)
    except:
        return []

def save_feedback(user_id, product_id, feedback, timestamp):
    """Save feedback to CSV file"""
    feedback_entry = {
        'MUDID': user_id,
        'Product_ID': product_id,
        'Feedback': feedback,  # 1 for thumbs up, -1 for thumbs down
        'Timestamp': timestamp
    }
    
    # Load existing feedback or create new
    try:
        feedback_df = pd.read_csv('feedback.csv')
        feedback_df = pd.concat([feedback_df, pd.DataFrame([feedback_entry])], ignore_index=True)
    except FileNotFoundError:
        feedback_df = pd.DataFrame([feedback_entry])
    
    feedback_df.to_csv('feedback.csv', index=False)
    st.session_state.feedback_data.append(feedback_entry)

def display_shap_explanation(shap_data, product_id):
    """Display SHAP explanation for a product"""
    try:
        shap_list = ast.literal_eval(shap_data)
        for shap_dict in shap_list:
            if product_id in shap_dict:
                features = shap_dict[product_id]
                
                st.write("**Feature Explanations:**")
                for feature in features[:3]:  # Show top 3 features
                    impact = feature.get('impact', 0)
                    feature_name = feature.get('feature', 'Unknown')
                    value = feature.get('value', 0)
                    
                    # Color code based on impact
                    color = "green" if impact > 0.02 else "orange" if impact > 0.01 else "red"
                    st.write(f"- **{feature_name}**: Impact {impact:.3f} ::{color}[●]")
                break
    except:
        st.write("No detailed explanation available")

def main():
    st.title("🎯 Product Recommendation System")
    st.markdown("---")
    
    # File upload section
    st.header("📁 Upload Recommendation Data")
    uploaded_file = st.file_uploader(
        "Choose your recommendation CSV file",
        type="csv",
        help="Upload your recommendations.csv file containing user recommendations"
    )
    
    # Load data
    df = load_data(uploaded_file)
    
    if df is None:
        st.stop()
    
    # Display file info
    if uploaded_file is not None:
        st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
        st.info(f"📊 Data contains {len(df)} users and {df.shape[1]} columns")
    else:
        st.info("📝 Using sample data for demonstration. Upload your CSV file to use real data.")
    
    # Show data preview
    with st.expander("📋 Preview Data Structure", expanded=False):
        st.dataframe(df.head(2), use_container_width=True)
        st.write("**Columns:**", list(df.columns))
    
    st.markdown("---")
    
    # Sidebar for user input
    st.sidebar.header("User Input")
    
    # User ID input
    available_users = df['MUDID'].unique().tolist()
    user_input = st.sidebar.text_input("Enter your User ID:", value="ai730048")
    
    # Search/filter options
    search_query = st.sidebar.text_input("Search for specific recommendations:", "")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"Recommendations for User: {user_input}")
        
        # Check if user exists in data
        user_data = df[df['MUDID'] == user_input]
        
        if user_data.empty:
            st.warning(f"No recommendations found for user {user_input}")
            st.info("Available users: " + ", ".join(available_users))
        else:
            # Get user's recommendations
            user_row = user_data.iloc[0]
            recommended_products = parse_list_string(user_row['Recommended_Product'])
            final_scores = parse_list_string(user_row['Final_Score'])
            rf_scores = parse_list_string(user_row['RF_Score'])
            cf_scores = parse_list_string(user_row['CF_Score'])
            
            # Filter products based on search query
            if search_query:
                filtered_products = [p for p in recommended_products if search_query in str(p)]
            else:
                filtered_products = recommended_products
            
            if not filtered_products:
                st.warning("No products match your search criteria")
            else:
                st.write(f"Found {len(filtered_products)} recommendations:")
                
                # Display recommendations
                for i, product_id in enumerate(filtered_products):
                    if product_id in recommended_products:
                        original_index = recommended_products.index(product_id)
                        
                        with st.expander(f"📦 Product ID: {product_id} (Score: {final_scores[original_index]:.2f})", expanded=True):
                            col_a, col_b, col_c = st.columns([2, 1, 1])
                            
                            with col_a:
                                st.write(f"**Final Score:** {final_scores[original_index]:.3f}")
                                st.write(f"**RF Score:** {rf_scores[original_index]:.3f}")
                                st.write(f"**CF Score:** {cf_scores[original_index]:.3f}")
                                
                                # Display SHAP explanation
                                display_shap_explanation(user_row['SHAP'], product_id)
                            
                            with col_b:
                                if st.button("👍", key=f"up_{product_id}", help="Thumbs Up"):
                                    save_feedback(user_input, product_id, 1, datetime.now())
                                    st.success("Thanks for your feedback!")
                                    st.rerun()
                            
                            with col_c:
                                if st.button("👎", key=f"down_{product_id}", help="Thumbs Down"):
                                    save_feedback(user_input, product_id, -1, datetime.now())
                                    st.success("Thanks for your feedback!")
                                    st.rerun()
    
    with col2:
        st.header("📊 Feedback Summary")
        
        # Load and display feedback stats
        try:
            feedback_df = pd.read_csv('feedback.csv')
            if not feedback_df.empty:
                user_feedback = feedback_df[feedback_df['MUDID'] == user_input]
                
                if not user_feedback.empty:
                    st.write("**Your Recent Feedback:**")
                    for _, row in user_feedback.tail(5).iterrows():
                        emoji = "👍" if row['Feedback'] == 1 else "👎"
                        st.write(f"{emoji} Product {row['Product_ID']}")
                
                # Overall stats
                st.write("**Overall Statistics:**")
                total_feedback = len(feedback_df)
                positive_feedback = len(feedback_df[feedback_df['Feedback'] == 1])
                negative_feedback = len(feedback_df[feedback_df['Feedback'] == -1])
                
                st.metric("Total Feedback", total_feedback)
                st.metric("Positive", positive_feedback)
                st.metric("Negative", negative_feedback)
                
                if total_feedback > 0:
                    satisfaction_rate = (positive_feedback / total_feedback) * 100
                    st.metric("Satisfaction Rate", f"{satisfaction_rate:.1f}%")
        except FileNotFoundError:
            st.info("No feedback data available yet")
    
    # Footer
    st.markdown("---")
    st.markdown("### Data Management")
    
    col_x, col_y = st.columns(2)
    
    with col_x:
        if st.button("📥 Download Feedback Data"):
            try:
                feedback_df = pd.read_csv('feedback.csv')
                st.download_button(
                    label="Download CSV",
                    data=feedback_df.to_csv(index=False),
                    file_name=f"feedback_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            except FileNotFoundError:
                st.warning("No feedback data to download")
    
    with col_y:
        if st.button("🔄 Refresh Data"):
            st.rerun()

if __name__ == "__main__":
    main()
