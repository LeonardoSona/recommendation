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

def save_feedback(user_id, product_id, feedback):
    """Save or update feedback to CSV file (latest vote only)"""
    feedback_entry = {
        'MUDID': user_id,
        'Product_ID': product_id,
        'Feedback': feedback  # 1 for thumbs up, -1 for thumbs down, 0 to remove vote
    }
    
    # Load existing feedback or create new
    try:
        feedback_df = pd.read_csv('feedback.csv')
        
        # Check if this user-product combination exists
        mask = (feedback_df['MUDID'] == user_id) & (feedback_df['Product_ID'] == product_id)
        
        if mask.any():
            # Update existing vote
            if feedback == 0:
                # Remove vote entirely
                feedback_df = feedback_df[~mask]
            else:
                # Update existing vote
                feedback_df.loc[mask, 'Feedback'] = feedback
        else:
            # Add new vote (only if not removing)
            if feedback != 0:
                feedback_df = pd.concat([feedback_df, pd.DataFrame([feedback_entry])], ignore_index=True)
    
    except FileNotFoundError:
        # Create new file (only if not removing)
        if feedback != 0:
            feedback_df = pd.DataFrame([feedback_entry])
        else:
            feedback_df = pd.DataFrame(columns=['MUDID', 'Product_ID', 'Feedback'])
    
    feedback_df.to_csv('feedback.csv', index=False)

def get_user_vote(user_id, product_id):
    """Get current vote for user-product pair"""
    try:
        feedback_df = pd.read_csv('feedback.csv')
        mask = (feedback_df['MUDID'] == user_id) & (feedback_df['Product_ID'] == product_id)
        if mask.any():
            return feedback_df.loc[mask, 'Feedback'].iloc[0]
        return 0  # No vote
    except FileNotFoundError:
        return 0  # No vote

def extract_user_from_text(text_input, available_users):
    """Extract user ID from natural language text input"""
    if not text_input.strip():
        return None, None
    
    text_lower = text_input.lower().strip()
    
    # Direct user ID check - look for exact matches
    for user in available_users:
        if str(user).lower() in text_lower:
            return user, f"Found user ID: {user}"
    
    # Look for partial matches (at least 4 characters)
    for user in available_users:
        user_str = str(user).lower()
        if len(user_str) >= 4:
            for i in range(len(user_str) - 3):
                substring = user_str[i:i+4]
                if substring in text_lower:
                    return user, f"Matched partial ID: {user}"
    
    # Common patterns
    patterns = [
        "recommend", "suggestion", "show", "get", "find", "what", "give me"
    ]
    
    if any(pattern in text_lower for pattern in patterns):
        return None, "I understand you want recommendations, but I need a user ID. Try including a user ID in your request or use the dropdown below."
    
    # Build available users sample
    available_sample = ', '.join(map(str, available_users[:3]))
    if len(available_users) > 3:
        available_sample += "..."
    
    return None, f"I couldn't find a matching user ID in your request. Available users: {available_sample}"

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
    st.sidebar.header("🤖 Ask for Recommendations")
    
    # Natural language text input
    text_query = st.sidebar.text_area(
        "💬 Describe what you want:",
        placeholder="e.g., 'Show me recommendations for ai730048' or 'What products would you suggest for user ai730048?'",
        height=100,
        help="You can ask in natural language! Include a user ID in your request."
    )
    
    # Process text input
    available_users = df['MUDID'].unique().tolist()
    selected_user_from_text = None
    text_feedback = None
    
    if text_query.strip():
        selected_user_from_text, text_feedback = extract_user_from_text(text_query, available_users)
        
        if selected_user_from_text:
            st.sidebar.success(text_feedback)
        else:
            st.sidebar.warning(text_feedback)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Or Select Manually")
    
    # Add search functionality for users
    user_search = st.sidebar.text_input("🔍 Search Users:", placeholder="Type to filter users...")
    
    # Filter users based on search
    if user_search:
        filtered_users = [user for user in available_users if user_search.lower() in str(user).lower()]
    else:
        filtered_users = available_users
    
    # User dropdown
    if filtered_users:
        # Determine default selection
        if selected_user_from_text and selected_user_from_text in filtered_users:
            default_index = filtered_users.index(selected_user_from_text)
        elif "ai730048" in filtered_users:
            default_index = filtered_users.index("ai730048")
        else:
            default_index = 0
        
        user_input = st.sidebar.selectbox(
            "Select User ID:",
            options=filtered_users,
            index=default_index,
            help=f"Found {len(filtered_users)} users"
        )
    else:
        st.sidebar.warning("No users match your search")
        user_input = None
    
    # Override with text selection if available
    if selected_user_from_text:
        user_input = selected_user_from_text
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if user_input is None:
            st.warning("Please ask for recommendations in the text area or select a user from the sidebar")
            st.info("💡 **Try these examples:**")
            st.code("Show me recommendations for ai730048")
            st.code("What products would you suggest for user ai730048?")
            st.code("Get recommendations for ai730")
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
                    
                    # Get current vote status
                    current_vote = get_user_vote(user_input, product_id)
                    
                    with thumb_col1:
                        # Determine button style based on current vote
                        if current_vote == 1:
                            button_type = "primary"
                            button_text = "👍"
                        else:
                            button_type = "secondary"
                            button_text = "👍"
                        
                        if st.button(button_text, key=f"up_{product_id}", help="Like this recommendation", 
                                   type=button_type, use_container_width=True):
                            # Toggle logic: if already liked, remove vote; otherwise set to like
                            new_vote = 0 if current_vote == 1 else 1
                            save_feedback(user_input, product_id, new_vote)
                            st.rerun()
                    
                    with thumb_col2:
                        # Determine button style based on current vote
                        if current_vote == -1:
                            button_type = "primary"
                            button_text = "👎"
                        else:
                            button_type = "secondary" 
                            button_text = "👎"
                        
                        if st.button(button_text, key=f"down_{product_id}", help="Dislike this recommendation", 
                                   type=button_type, use_container_width=True):
                            # Toggle logic: if already disliked, remove vote; otherwise set to dislike
                            new_vote = 0 if current_vote == -1 else -1
                            save_feedback(user_input, product_id, new_vote)
                            st.rerun()
                
                # Add SHAP explanation in a subtle way
                if i < 3:  # Show SHAP for top 3 only to avoid clutter
                    with st.expander(f"🔍 Why Product {product_id}?", expanded=False):
                        display_shap_explanation(user_row['SHAP'], product_id)
                
                # Add separator between products
                if i < len(recommended_products) - 1:
                    st.divider()
    
    with col2:
        st.header("📊 Your Feedback")
        
        # Load and display user-specific feedback stats
        try:
            feedback_df = pd.read_csv('feedback.csv')
            user_feedback = feedback_df[feedback_df['MUDID'] == user_input]
            
            if not user_feedback.empty:
                st.write("**Your Recent Votes:**")
                
                # Show recent votes with product info
                for _, row in user_feedback.tail(5).iterrows():
                    emoji = "👍" if row['Feedback'] == 1 else "👎"
                    st.write(f"{emoji} Product {row['Product_ID']}")
                
                # User-specific stats
                st.write("**Your Statistics:**")
                total_votes = len(user_feedback)
                positive_votes = len(user_feedback[user_feedback['Feedback'] == 1])
                negative_votes = len(user_feedback[user_feedback['Feedback'] == -1])
                
                st.metric("Total Votes", total_votes)
                col_pos, col_neg = st.columns(2)
                with col_pos:
                    st.metric("👍 Likes", positive_votes)
                with col_neg:
                    st.metric("👎 Dislikes", negative_votes)
                
                if total_votes > 0:
                    satisfaction_rate = (positive_votes / total_votes) * 100
                    st.metric("Your Satisfaction", f"{satisfaction_rate:.0f}%")
            else:
                st.info("No votes yet. Start rating recommendations!")
                
        except FileNotFoundError:
            st.info("No feedback data available yet")
    
    # Footer
    st.markdown("---")
    st.markdown("### Data Management")
    
    col_x, col_y = st.columns(2)
    
    with col_x:
        if st.button("📥 Download Your Feedback"):
            try:
                feedback_df = pd.read_csv('feedback.csv')
                user_feedback = feedback_df[feedback_df['MUDID'] == user_input]
                if not user_feedback.empty:
                    st.download_button(
                        label="Download Your Data",
                        data=user_feedback.to_csv(index=False),
                        file_name=f"feedback_{user_input}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No feedback data to download for this user")
            except FileNotFoundError:
                st.warning("No feedback data to download")
    
    with col_y:
        if st.button("🔄 Refresh Data"):
            st.rerun()

if __name__ == "__main__":
    main()
