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
    
    # User ID dropdown with search
    available_users = df['MUDID'].unique().tolist()
    
    # Add search functionality for users
    user_search = st.sidebar.text_input("🔍 Search Users:", placeholder="Type to filter users...")
    
    # Filter users based on search
    if user_search:
        filtered_users = [user for user in available_users if user_search.lower() in str(user).lower()]
    else:
        filtered_users = available_users
    
    # User dropdown
    if filtered_users:
        default_index = 0
        if "ai730048" in filtered_users:
            default_index = filtered_users.index("ai730048")
        
        user_input = st.sidebar.selectbox(
            "📋 Select User ID:",
            options=filtered_users,
            index=default_index,
            help=f"Found {len(filtered_users)} users"
        )
    else:
        st.sidebar.warning("No users match your search")
        user_input = None
    

    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if user_input is None:
            st.warning("Please select a user from the sidebar")
            st.stop()
            
        st.header(f"Recommendations for User: {user_input}")
        
        # Check if user exists in data
        user_data = df[df['MUDID'] == user_input]
        
        if user_data.empty:
            st.warning(f"No recommendations found for user {user_input}")
        else:
            # Get user's recommendations
            user_row = user_data.iloc[0]
            recommended_products = parse_list_string(user_row['Recommended_Product'])
            final_scores = parse_list_string(user_row['Final_Score'])
            rf_scores = parse_list_string(user_row['RF_Score'])
            cf_scores = parse_list_string(user_row['CF_Score'])
            
            total_products = len(recommended_products)
            st.info(f"📦 Found {total_products} recommendations")
            
            # Add column headers
            header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([0.5, 1.5, 1, 1, 1, 1.5])
            
            with header_col1:
                st.write("**Rank**")
            with header_col2:
                st.write("**Product ID**")
            with header_col3:
                st.write("**Final Score**")
            with header_col4:
                st.write("**RF Score**")
            with header_col5:
                st.write("**CF Score**")
            with header_col6:
                st.write("**Your Feedback**")
            
            st.divider()
            
            # Display recommendations inline
            for i, product_id in enumerate(recommended_products):
                # Create inline display with columns
                col_rank, col_product, col_final, col_rf, col_cf, col_thumbs = st.columns([0.5, 1.5, 1, 1, 1, 1.5])
                
                with col_rank:
                    st.write(f"**#{i+1}**")
                
                with col_product:
                    st.write(f"**Product {product_id}**")
                
                with col_final:
                    score_color = "🟢" if final_scores[i] >= 0.7 else "🟡" if final_scores[i] >= 0.4 else "🔴"
                    st.write(f"{score_color} {final_scores[i]:.3f}")
                
                with col_rf:
                    st.write(f"{rf_scores[i]:.3f}")
                
                with col_cf:
                    st.write(f"{cf_scores[i]:.3f}")
                
                with col_thumbs:
                    thumb_col1, thumb_col2 = st.columns(2)
                    
                    with thumb_col1:
                        if st.button("👍", key=f"up_{product_id}", help="Like this recommendation"):
                            save_feedback(user_input, product_id, 1, datetime.now())
                            st.success("👍")
                            st.rerun()
                    
                    with thumb_col2:
                        if st.button("👎", key=f"down_{product_id}", help="Dislike this recommendation"):
                            save_feedback(user_input, product_id, -1, datetime.now())
                            st.success("👎")
                            st.rerun()
                
                # Add SHAP explanation in a subtle way
                if i < 3:  # Show SHAP for top 3 only to avoid clutter
                    with st.expander(f"🔍 Why Product {product_id}?", expanded=False):
                        display_shap_explanation(user_row['SHAP'], product_id)
                
                # Add separator between products
                if i < len(recommended_products) - 1:
                    st.divider()
    
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
