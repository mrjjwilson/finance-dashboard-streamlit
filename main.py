import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="Simple Finance App", page_icon="💰", layout="wide")

category_file = "categories.json"


# Storing Session State
if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }

if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)
        
def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)
        
def categorize_transactions(df):
    df["Category"] = "Uncategorized"
    
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
        
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        
        for idx, row in df.iterrows():
            description = row["Description"].lower().strip()
            if description in lowered_keywords:
                df.at[idx, "Category"] = category
    return df
                

def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        return categorize_transactions(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False


def main():
    st.title("Simple Finance Dashboard")

    uploaded_file = st.file_uploader("Upload your transaction CSV file", type=["csv"])

    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            debits_df = df[df["Amount"] < 0 ].copy()
            credits_df = df[df["Amount"] > 0 ].copy()

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Income (Credits)"])
            
            with tab1:
                # Add Debits to session state
                st.session_state.debits_df = debits_df.copy()
                
                # Expense Summary
                st.subheader("Expense Summary")
                category_totals = st.session_state.debits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending=False)
                
                st.dataframe(
                    category_totals,
                    column_config={
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f USD")
                    },
                    use_container_width=False,
                    hide_index=True
                    )
                
                # Create Add Button
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")
                
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()
                
                # Create Expenses Section
                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[["Category", "Date", "Amount", "Description", "Payee Account Number"]],
                    column_config={
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )
                
                # Create Save Button
                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if row["Category"] == st.session_state.debits_df.at[idx, "Category"]:
                            continue
                        
                        # TODO: DESCRIPTION IS NOT UNIQUE, THE PAYEE NUMBER IS UNIQUE, CURRENT BUG IS NOT ALLOWING ME TO SPLIT TRANSFERS TO 3 DIFFERENT ACCOUNTS
                        # LEARN HOW TO DEBUG CODE IN STREAMLIT
                        description = row["Description"]
                        payee_account_number = row["Payee Account Number"]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, description)
                        
                # Create Chart
                fig = px.pie(
                    category_totals,
                    values="Amount",
                    names="Category",
                    title="Expenses by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                
            with tab2:
                st.subheader("Payments Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payments", f"{total_payments:,.2f} USD")
                st.write(credits_df)


if __name__ == "__main__":
    main()