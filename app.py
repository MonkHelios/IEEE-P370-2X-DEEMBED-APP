
import streamlit as st
import skrf as rf
from skrf.calibration import IEEEP370_SE_NZC_2xThru
import matplotlib.pyplot as plt
import io
import tempfile
import os
import datetime # Import datetime for current date

st.set_page_config(page_title="IEEE P370 De-Embedding Engine", layout="wide", menu_items={'About': ''})

def plot_s_params(network, title, comparison_network=None):
    '''Plots S-parameters individually for verification, with optional comparison network.'''
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(title, fontsize=16)
    axes = axes.flatten()

    s_params_map = {
        'S11': 's11', 'S21': 's21', 'S12': 's12', 'S22': 's22'
    }

    for i, (label_key, s_param_attr) in enumerate(s_params_map.items()):
        ax = axes[i]
        current_s_param = getattr(network, s_param_attr, None)

        if current_s_param is not None:
            # Plot the primary network's S-parameter
            current_s_param.plot_s_db(ax=ax, label=f'{label_key} ({network.name if network.name else "1x"})')

            # Plot the comparison network's S-parameter if provided
            if comparison_network:
                comp_s_param = getattr(comparison_network, s_param_attr, None)
                if comp_s_param is not None:
                    comp_s_param.plot_s_db(ax=ax, label=f'{label_key} ({comparison_network.name if comparison_network.name else "2x Thru"})', color='red', linestyle='--')

            ax.set_title(f'{label_key} (dB)')
            ax.grid(True)
            ax.legend()
        else:
            ax.set_title(f'{label_key} (Not available)')
            ax.text(0.5, 0.5, 'N/A', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=20, color='gray')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def plot_tdr(network, title):
    '''Plots Time Domain Reflectometry (Impulse Response) with Hamming windowing.'''
    fig, ax = plt.subplots(figsize=(8, 4))
    # skrf impulse response with Hamming window
    network.plot_s_time_impulse(ax=ax, window='hamming')
    ax.set_title(f"TDR Impulse Response (Hamming) - {title}")
    ax.grid(True)
    return fig

def load_touchstone(uploaded_file):
    '''Safely loads a Touchstone file from Streamlit's in-memory buffer.'''
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".s2p") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        try:
            ntwk = rf.Network(tmp_path)
            os.remove(tmp_path)
            return ntwk
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")
            os.remove(tmp_path)
    return None

def generate_touchstone_comments(file_description):
    '''Generates standard comments for IEEE P370 compliant Touchstone files.'''
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    comments = [
        "IEEE-P370 Compliant De-embedding Software version 1.0",
        "Deembedding/AFR applied",
        "Author: Aditya Mukherjee (mukherjee.tech)",
        f"Define the type of S-parameter file here in short - {file_description}",
        "NUMBER_PORTS: 2",
        f"Date: {current_date}",
        "S2P File: Measurements: S11,S21,S12,S22:"
    ]
    return comments

def process_touchstone_for_tabs(file_path):
    '''Reads a Touchstone file, replaces space delimiters with tabs in data lines, and overwrites the file.'''
    with open(file_path, "r") as f:
        content = f.read()

    processed_lines = []
    for line in content.splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            processed_lines.append('')
            continue

        if stripped_line.startswith('!') or stripped_line.startswith('#'):
            processed_lines.append(line)
        else:
            parts = stripped_line.split()
            processed_lines.append("\t".join(parts))

    with open(file_path, "w") as f:
        f.write("\n".join(processed_lines))


st.title("IEEE P370 Fixture De-Embedding")
st.markdown("---")

st.header("1. Fixture Configuration")
# st.image("P370_Block.JPG", caption="Block Diagram: Fixture A - DUT - Fixture B", width=700)
fixture_type = st.radio(
    "How many distinct fixture types require de-embedding?",
    options=[1, 2],
    format_func=lambda x: "1 (Symmetric: Fixture A = Fixture B)" if x == 1 else "2 (Asymmetric: Fixture A ≠ Fixture B)"
)

st.header("2. Calibration Standards (2X Thru)")
thru_networks = []

if fixture_type == 1:
    st.markdown("**Required File:** 1x Symmetric 2X-Thru Standard (`[Fixture A] <--> [Fixture A]`) ")
    thru_a = st.file_uploader("Upload 2X Thru for Fixture A (.s2p, .s4p)", type=['s2p', 's4p'], key="thru_a")
    if thru_a:
        ntwk = load_touchstone(thru_a)
        if ntwk is not None:
            ntwk.name = "2x Thru A"
            if st.button("Plot 2X Thru Data", key="plot_thru_a"):
                st.pyplot(plot_s_params(ntwk, "2X Thru - Fixture A"))
            thru_networks.append(ntwk)
else:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Required File:** 2X-Thru Standard A (`[Fixture A] <--> [Fixture A]`) ")
        thru_a = st.file_uploader("Upload 2X Thru for Fixture A", type=['s2p', 's4p'], key="thru_a_2")
        if thru_a:
            ntwk = load_touchstone(thru_a)
            if ntwk is not None:
                ntwk.name = "2x Thru A"
                if st.button("Plot Standard A", key="plot_thru_a_2"):
                    st.pyplot(plot_s_params(ntwk, "2X Thru A-A"))
                thru_networks.append(ntwk)
    with col2:
        st.markdown("**Required File:** 2X-Thru Standard B (`[Fixture B] <--> [Fixture B]`) ")
        thru_b = st.file_uploader("Upload 2X Thru for Fixture B", type=['s2p', 's4p'], key="thru_b")
        if thru_b:
            ntwk = load_touchstone(thru_b)
            if ntwk is not None:
                ntwk.name = "2x Thru B"
                if st.button("Plot Standard B", key="plot_thru_b"):
                    st.pyplot(plot_s_params(ntwk, "2X Thru B-B"))
                thru_networks.append(ntwk)

st.markdown("---")

st.header("2.5. Generate 1x S-Parameters")
if len(thru_networks) > 0:
    if fixture_type == 1 and len(thru_networks) == 1:
        if st.button("Generate 1x S-Parameter for Fixture A (Symmetric)", key="generate_1x_s_params_sym"):
            try:
                deembedder_1x = IEEEP370_SE_NZC_2xThru(dummy_2xthru=thru_networks[0], name='1x_symmetric_deembed')
                fixture_a_1x = deembedder_1x.s_side1
                fixture_a_1x.name = "Fixture A (1x)"
                st.session_state['fixture_a_1x'] = fixture_a_1x
                st.success("1x S-Parameter for Fixture A generated.")
                if 'fixture_b_1x' in st.session_state:
                    del st.session_state['fixture_b_1x']
            except Exception as e:
                st.error(f"Error generating 1x S-Parameter for Fixture A: {e}")
    elif fixture_type == 2 and len(thru_networks) == 2:
        col_gen_a, col_gen_b = st.columns(2)
        with col_gen_a:
            if st.button("Generate 1x S-Parameter for Fixture A", key="generate_1x_s_params_a"):
                try:
                    deembed_a_1x = IEEEP370_SE_NZC_2xThru(dummy_2xthru=thru_networks[0], name='1x_a_split')
                    fixture_a_1x = deembed_a_1x.s_side1
                    fixture_a_1x.name = "Fixture A (1x)"
                    st.session_state['fixture_a_1x'] = fixture_a_1x
                    st.success("1x S-Parameter for Fixture A generated.")
                except Exception as e:
                    st.error(f"Error generating 1x S-Parameter for Fixture A: {e}")
        with col_gen_b:
            if st.button("Generate 1x S-Parameter for Fixture B", key="generate_1x_s_params_b"):
                try:
                    deembed_b_1x = IEEEP370_SE_NZC_2xThru(dummy_2xthru=thru_networks[1], name='1x_b_split')
                    fixture_b_1x = deembed_b_1x.s_side1
                    fixture_b_1x.name = "Fixture B (1x)"
                    st.session_state['fixture_b_1x'] = fixture_b_1x
                    st.success("1x S-Parameter for Fixture B generated.")
                except Exception as e:
                    st.error(f"Error generating 1x S-Parameter for Fixture B: {e}")

if 'fixture_a_1x' in st.session_state and st.session_state['fixture_a_1x'] is not None:
    st.subheader("Generated Fixture A (1x) S-Parameters")
    if st.button("Plot Fixture A (1x) vs 2x Thru A", key="plot_1x_a"):
        if len(thru_networks) > 0:
            st.pyplot(plot_s_params(st.session_state['fixture_a_1x'], "Generated Fixture A (1x) S-Parameters vs 2x Thru A", comparison_network=thru_networks[0]))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".s2p") as tmp_file:
        st.session_state['fixture_a_1x'].comments = generate_touchstone_comments("1X Fixture A")
        st.session_state['fixture_a_1x'].write_touchstone(dir='', filename=tmp_file.name, form='ri')
        process_touchstone_for_tabs(tmp_file.name)
        with open(tmp_file.name, "rb") as f: file_bytes_a = f.read()
    st.download_button("Download Fixture A (1x) S-Parameters", data=file_bytes_a, file_name="FixtureA_1x.s2p", key="dl_a")
    os.remove(tmp_file.name)

if 'fixture_b_1x' in st.session_state and st.session_state['fixture_b_1x'] is not None:
    st.subheader("Generated Fixture B (1x) S-Parameters")
    if st.button("Plot Fixture B (1x) vs 2x Thru B", key="plot_1x_b"):
        if fixture_type == 2 and len(thru_networks) > 1:
            st.pyplot(plot_s_params(st.session_state['fixture_b_1x'], "Generated Fixture B (1x) S-Parameters vs 2x Thru B", comparison_network=thru_networks[1]))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".s2p") as tmp_file:
        st.session_state['fixture_b_1x'].comments = generate_touchstone_comments("1X Fixture B")
        st.session_state['fixture_b_1x'].write_touchstone(dir='', filename=tmp_file.name, form='ri')
        process_touchstone_for_tabs(tmp_file.name)
        with open(tmp_file.name, "rb") as f: file_bytes_b = f.read()
    st.download_button("Download Fixture B (1x) S-Parameters", data=file_bytes_b, file_name="FixtureB_1x.s2p", key="dl_b")
    os.remove(tmp_file.name)

st.markdown("---")
st.header("3. Composite Measurement (FIX-DUT-FIX)")
composite_file = st.file_uploader("Upload FIX-DUT-FIX measurement", type=['s2p', 's4p'], key="comp")
if composite_file:
    composite_ntwk = load_touchstone(composite_file)
    if composite_ntwk and st.button("Plot Composite Data"):
        st.pyplot(plot_s_params(composite_ntwk, "Raw Composite S-Parameters"))

st.markdown("---")
st.header("4. Execution & Extraction")
if st.button("Run IEEE P370 De-embedding", type="primary"):
    if not composite_file or len(thru_networks) != fixture_type:
        st.error("Missing required files.")
    else:
        try:
            if fixture_type == 1:
                deembedder = IEEEP370_SE_NZC_2xThru(dummy_2xthru=thru_networks[0])
                fixture_l, fixture_r = deembedder.s_side1, deembedder.s_side2
            else:
                fixture_l = IEEEP370_SE_NZC_2xThru(dummy_2xthru=thru_networks[0]).s_side1
                fixture_r = IEEEP370_SE_NZC_2xThru(dummy_2xthru=thru_networks[1]).s_side1

            dut_extracted = fixture_l.inv ** composite_ntwk ** fixture_r.inv
            st.success("De-embedding completed.")
            st.pyplot(plot_s_params(dut_extracted, "Extracted DUT"))
            
            dut_extracted.comments = generate_touchstone_comments("De-embedded DUT")
            dut_extracted.write_touchstone(dir='', filename="extracted_dut.s2p", form='ri')
            process_touchstone_for_tabs("extracted_dut.s2p")
            with open("extracted_dut.s2p", "rb") as f: st.download_button("Download Result", f, "DeEmbedded_DUT.s2p")
            os.remove("extracted_dut.s2p")
        except Exception as e: st.error(f"Execution failed: {e}")
