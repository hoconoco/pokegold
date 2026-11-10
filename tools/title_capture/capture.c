/* capture <rom> <outdir> <start_frame> <frames> <shot_every>
 *
 * Runs a ROM with libmgba (no BIOS, no save file) for <frames> frames, presses START for 6 frames
 * at <start_frame> (skips the intro, as the first screen's live preview did), and writes
 *   <outdir>/audio.raw   every audio sample from frame 0 on, stereo s16le at the core's rate
 *   <outdir>/video.raw   every <shot_every>-th frame, w*h RGBX bytes each
 *   <outdir>/sig.raw     every frame's mean R, G, B (3 bytes per frame)
 *   <outdir>/info.txt    rate, width, height, frames, shot_every, start_frame, samples
 * tools/make_titles.py reads these and cuts the title screen still and its music out of them.
 */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <mgba-util/audio-buffer.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void quiet(struct mLogger* l, int cat, enum mLogLevel lv, const char* fmt, va_list a) {
	(void) l; (void) cat; (void) lv; (void) fmt; (void) a;
}

int main(int argc, char** argv) {
	if (argc != 6) { fprintf(stderr, "usage: capture <rom> <outdir> <start_frame> <frames> <shot_every>\n"); return 2; }
	const char* rom = argv[1];
	const char* out = argv[2];
	int start = atoi(argv[3]), total = atoi(argv[4]), every = atoi(argv[5]);
	static struct mLogger logger = { .log = quiet };
	mLogSetDefaultLogger(&logger);

	struct mCore* core = mCoreFind(rom);
	if (!core) { fprintf(stderr, "no core for %s\n", rom); return 1; }
	core->init(core);
	mCoreInitConfig(core, NULL);
	static mColor video[256 * 224];
	core->setVideoBuffer(core, video, 256);
	core->setAudioBufferSize(core, 16384);
	core->opts.volume = 0x100;
	core->opts.mute = false;
	mCoreLoadConfig(core);
	if (!mCoreLoadFile(core, rom)) { fprintf(stderr, "cannot load %s\n", rom); return 1; }
	core->reset(core);

	char path[1024];
	snprintf(path, sizeof path, "%s/audio.raw", out);
	FILE* fa = fopen(path, "wb");
	snprintf(path, sizeof path, "%s/video.raw", out);
	FILE* fv = fopen(path, "wb");
	snprintf(path, sizeof path, "%s/sig.raw", out);
	FILE* fs = fopen(path, "wb");
	if (!fa || !fv || !fs) { fprintf(stderr, "cannot write in %s\n", out); return 1; }

	unsigned w = 0, h = 0;
	long samples = 0;
	static int16_t buf[16384 * 2];
	struct mAudioBuffer* ab = core->getAudioBuffer(core);
	for (int f = 0; f < total; ++f) {
		core->setKeys(core, (f >= start && f < start + 6) ? (1 << 3) : 0);  /* bit 3 = START (GB and GBA) */
		core->runFrame(core);
		size_t n;
		while ((n = mAudioBufferAvailable(ab)) > 0) {
			if (n > 16384) n = 16384;
			n = mAudioBufferRead(ab, buf, n);
			fwrite(buf, sizeof(int16_t) * 2, n, fa);
			samples += (long) n;
		}
		core->currentVideoSize(core, &w, &h);
		if (f % every == 0)
			for (unsigned y = 0; y < h; ++y) fwrite(&video[y * 256], 4, w, fv);
		/* mean R, G, B of every frame — where the title screen fades in and out */
		unsigned long sum[3] = { 0, 0, 0 };
		for (unsigned y = 0; y < h; ++y)
			for (unsigned x = 0; x < w; ++x)
				for (int c = 0; c < 3; ++c) sum[c] += ((const uint8_t*) &video[y * 256 + x])[c];
		uint8_t mean[3];
		for (int c = 0; c < 3; ++c) mean[c] = (uint8_t) (sum[c] / (w * h));
		fwrite(mean, 1, 3, fs);
	}
	fclose(fa);
	fclose(fv);
	fclose(fs);
	snprintf(path, sizeof path, "%s/info.txt", out);
	FILE* fi = fopen(path, "w");
	fprintf(fi, "rate %u\nwidth %u\nheight %u\nframes %d\nshot_every %d\nstart_frame %d\nsamples %ld\n",
		core->audioSampleRate(core), w, h, total, every, start, samples);
	fclose(fi);
	core->deinit(core);
	return 0;
}
