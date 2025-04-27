import streamlit as st
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime
import base64

# Connect to MongoDB client
client = MongoClient("mongodb://localhost:27017/")
db = client["smart_prep"]
blogs_collection = db["blogs"]
comments_collection = db["Comment"]

def convert_image_to_base64(image_file):
    """Convert uploaded image to base64 for storage"""
    if image_file is not None:
        # Read the image file
        image_bytes = image_file.getvalue()
        # Encode the image bytes to base64
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
        return base64_encoded
    return None

def show_blog_section():
    from session_manager import navigate_to
    
    # ✅ Add "Back to Home" button at the top (Same as study_resources.py)
    if st.button("← Back to Home"):
        navigate_to("home")

    # Title with centered alignment
    st.markdown('<div style="text-align: center;"><h1>Smart Prep Blogs</h1></div>', unsafe_allow_html=True)

    # Blog Submission Form
    with st.expander("Create New Blog Post"):
        # Use unique key for each input to ensure reset
        col1, col2 = st.columns(2)
        with col1:
            blog_title = st.text_input("Blog Title", key="blog_title_input")
            current_username = st.session_state.get("user_session", "Guest")
            blog_author = st.text_input("Author Name", value=current_username, disabled=True, key="blog_author_input")

        with col2:
            blog_image = st.file_uploader("Upload Blog Image", type=['jpg', 'jpeg', 'png'], key="blog_image_upload")
            blog_category = st.selectbox(
                "Category",
                ["General", "Study Tips", "Exam Preparation", "Success Stories", "Career Guidance"],
                key="blog_category_select"
            )

        blog_content = st.text_area(
            "Blog Content (Markdown Supported)",
            key="blog_content_input",
            height=200
        )

        # Action buttons
        col_post, col_cancel = st.columns(2)
        with col_post:
            if st.button("Post Blog", key="post_blog_btn"):
                # Retrieve values directly from session state
                current_title = blog_title
                current_author = blog_author
                current_content = blog_content
                current_category = blog_category

                if current_title and current_content and current_author:
                    image_base64 = convert_image_to_base64(blog_image) if blog_image else None
                    
                    blogs_collection.insert_one({
                        "title": current_title,
                        "content": current_content,
                        "author": current_author,
                        "category": current_category,
                        "image": image_base64,
                        "timestamp": datetime.utcnow(),
                        "likes": 0,
                        "comments": []
                    })
                    st.success("✅ Blog posted successfully!")
                    
                    # Trigger a rerun to reset the form
                    st.rerun()
                else:
                    st.error("⚠️ Please fill all required fields!")
    col_sort, col_page = st.columns(2)
    with col_sort:
        sort_option = st.selectbox("Sort By", 
            ["Latest", "Most Liked", "Most Commented"])
    
    with col_page:
        page_size = st.selectbox("Posts per Page", [5, 10, 15, 20])

    # Sorting logic
    if sort_option == "Latest":
        sort_criteria = {"timestamp": -1}
    elif sort_option == "Most Liked":
        sort_criteria = {"likes": -1}
    else:
        sort_criteria = {"comments": -1}

    # Fetch blogs with sorting
    blogs = list(blogs_collection.find().sort(list(sort_criteria.items())).limit(page_size))

    # Instagram-style grid
    for blog in blogs:
        with st.container():
            # Blog header
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                st.markdown(f"**{blog['title']}**")
            with col2:
                # Robust category handling
                category = blog.get('category', 'Uncategorized')
                st.markdown(f"By: {blog.get('author', 'Anonymous')} | {category}")
            
            # Blog image (if exists)
            if blog.get('image'):
                try:
                    image_data = base64.b64decode(blog['image'])
                    st.image(image_data, use_container_width=True)
                except:
                    st.write("Image could not be displayed")

            # Blog content preview
            if len(blog['content']) > 300:
                st.markdown(blog['content'][:300] + "...")
                with st.expander("Show More"):
                    st.markdown(blog['content'])
            else:
                st.markdown(blog['content'])


            # Interaction buttons
            col_like, col_comment, col_actions = st.columns(3)
            
            with col_like:
                like_btn = st.button(f"👍 Likes: {blog.get('likes', 0)}", key=f"like_{blog['_id']}")
                if like_btn:
                    blogs_collection.update_one(
                        {"_id": blog['_id']}, 
                        {"$inc": {"likes": 1}}
                    )
                    st.rerun()

            with col_comment:
                if st.button("💬 Comments", key=f"comment_{blog['_id']}"):
                    st.session_state["current_blog_id"] = str(blog['_id'])
                    st.rerun()

            with col_actions:
                # Only show edit/delete for the blog author
                if blog.get('author', '') == st.session_state.get('user_session', ''):
                    action = st.selectbox("Actions", ["", "Edit", "Delete"], key=f"action_{blog['_id']}")
                    if action == "Delete":
                        if st.button("Confirm Delete", key=f"delete_{blog['_id']}"):
                            blogs_collection.delete_one({"_id": blog['_id']})
                            comments_collection.delete_many({"blog_id": str(blog['_id'])})
                            st.success("Blog deleted successfully!")
                            st.rerun()
                    elif action == "Edit":
                        # Open edit modal or form
                        with st.expander("Edit Blog"):
                            edit_title = st.text_input("Title", blog['title'], key=f"edit_title_{blog['_id']}")
                            edit_content = st.text_area("Content", blog['content'], key=f"edit_content_{blog['_id']}")
                            edit_category = st.selectbox(
                                "Category", 
                                ["General", "Study Tips", "Exam Preparation", "Success Stories", "Career Guidance", "Uncategorized"],
                                index=0,
                                key=f"edit_category_{blog['_id']}"
                            )
                            
                            if st.button("Update Blog", key=f"update_{blog['_id']}"):
                                blogs_collection.update_one(
                                    {"_id": blog['_id']},
                                    {"$set": {
                                        "title": edit_title,
                                        "content": edit_content,
                                        "category": edit_category
                                    }}
                                )
                                st.success("Blog updated successfully!")
                                st.rerun()

            # Comments Section (when a specific blog is selected)
            if "current_blog_id" in st.session_state and str(blog['_id']) == st.session_state["current_blog_id"]:
                st.markdown("---")
                st.subheader("Comments")
                
                # Fetch comments for this blog
                comments = list(comments_collection.find({"blog_id": str(blog['_id'])}))
                
                if comments:
                    for comment in comments:
                        st.write(f"👤 {comment.get('author', 'Anonymous')}: {comment.get('comment', 'No comment')}")
                
                # Add new comment
                current_username = st.session_state.get("user_session", "Guest")
                new_comment_author = st.text_input("Username", value=current_username, disabled=True, key=f"comment_author_{blog['_id']}")

                new_comment_text = st.text_area("Your Comment", key=f"comment_text_{blog['_id']}")
                
                if st.button("Post Comment", key=f"submit_comment_{blog['_id']}"):
                    if new_comment_author and new_comment_text:
                        comments_collection.insert_one({
                            "blog_id": str(blog['_id']),
                            "author": new_comment_author,
                            "comment": new_comment_text,
                            "timestamp": datetime.utcnow()
                        })
                        # Update comments count in blog
                        blogs_collection.update_one(
                            {"_id": blog['_id']}, 
                            {"$push": {"comments": new_comment_text}}
                        )
                        st.success("Comment added!")
                        st.rerun()

            st.markdown("---")

if __name__ == "__main__":
    st.error("This is a module and should not be run directly. Please run home.py instead.")